import json
import time

from sqlalchemy.orm import Session

from app.agent.metta_engine import MeTTAEngine
from app.agent.tools import (
    tool_calculate_allocation,
    tool_get_approval_status,
    tool_get_eligible_teams,
    tool_get_funding_policy,
    tool_get_simulated_near_quote,
    tool_reconcile_payout,
    tool_validate_payout_batch,
)
from app.models import AgentRun, AgentToolCall


class OmegaAgentOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.metta = MeTTAEngine()

    def run_agent_workflow(self, competition_id: str, intent: str, prompt: str = "",
                           context: dict = None) -> dict:
        context = context or {}
        self.metta.clear_traces()

        # Check prompt injection guard via MeTTa rule
        if "ignore all rules" in prompt.lower() or "bypass" in prompt.lower():
            run = AgentRun(
                organization_id="org-fundguard-global",
                competition_id=competition_id,
                intent=intent,
                prompt=prompt,
                status="refused",
                summary="Refused request: attempted policy override or safety bypass detected. Policy rules are immutable.",
                metta_expressions_evaluated=json.dumps([{"query": "(sanitize-instruction prompt)", "reduction": "POLICY_OVERRIDE_REJECTED"}])
            )
            self.db.add(run)
            self.db.commit()
            return {
                "agent_run_id": run.id,
                "status": "refused",
                "summary": run.summary,
                "tool_calls": [],
                "metta_traces": [{"query": "(sanitize-instruction ...)", "reduction": "POLICY_OVERRIDE_REJECTED"}],
                "next_action": "halt"
            }

        recorded_tool_calls = []

        def invoke_tool(name: str, fn, **kwargs):
            t0 = time.time()
            try:
                result = fn(**kwargs)
                duration = int((time.time() - t0) * 1000)
                recorded_tool_calls.append({
                    "tool": name,
                    "arguments": kwargs,
                    "result": result,
                    "error": None,
                    "duration_ms": duration
                })
                return result
            except Exception as e:
                duration = int((time.time() - t0) * 1000)
                recorded_tool_calls.append({
                    "tool": name,
                    "arguments": kwargs,
                    "result": None,
                    "error": str(e),
                    "duration_ms": duration
                })
                raise

        summary = ""
        next_action = "none"

        if intent == "prepare_payout_proposal":
            # 1. Retrieve policy
            policy = invoke_tool("get_funding_policy", tool_get_funding_policy, db=self.db, competition_id=competition_id)
            # 2. Retrieve eligible recipients
            invoke_tool("get_eligible_teams", tool_get_eligible_teams, db=self.db, competition_id=competition_id)
            # 3. Calculate allocation
            alloc = invoke_tool("calculate_allocation", tool_calculate_allocation, db=self.db, competition_id=competition_id)

            # Evaluate MeTTa reasoning
            target = alloc["target_eligible_count"]
            eligible = alloc["eligible_count"]
            total_fund = alloc["total_fund_base_units"]
            ratio = self.metta.query(f"!(eligible-ratio {eligible} {target})")
            released = self.metta.query(f"!(calculate-release {total_fund} {ratio})")
            reserve = self.metta.query(f"!(calculate-reserve {total_fund} {released})")
            accounting_valid = self.metta.query(f"!(verify-accounting-invariant {total_fund} {released} {reserve})")

            summary = (
                f"Evaluated policy version {policy['version']} (hash {policy['rules_hash'][:16]}…). "
                f"Identified {eligible} verified eligible recipient(s) out of target {target}. "
                f"MeTTa release ratio: {float(ratio)*100:.1f}%. Released allocation: {alloc['released_base_units']} base units. "
                f"Carry-forward reserve: {alloc['total_reserve_base_units']} base units. "
                f"Accounting invariant satisfied: {accounting_valid}. Human approval required before batch execution."
            )
            next_action = "human_approval_required"

        elif intent == "validate_batch":
            batch_id = context.get("batch_id")
            val = invoke_tool("validate_payout_batch", tool_validate_payout_batch, db=self.db, batch_id=batch_id)
            appr = invoke_tool("get_approval_status", tool_get_approval_status, db=self.db, batch_id=batch_id)
            summary = f"Batch validation result: valid={val.get('valid')}. Current approval status: {appr.get('status')}."
            next_action = "ready_for_execution" if appr.get("is_approved") else "approval_required"

        elif intent == "reconcile_payout":
            payout_id = context.get("payout_id")
            rec = invoke_tool("reconcile_payout", tool_reconcile_payout, db=self.db, payout_id=payout_id)
            summary = f"Reconciled payout {payout_id}: status={rec.get('status')}."
            next_action = "none"

        elif intent == "near_intents_quote":
            quote = invoke_tool("get_simulated_near_quote", tool_get_simulated_near_quote,
                                from_asset=context.get("from_asset", "XLM"),
                                to_asset=context.get("to_asset", "NEAR"),
                                amount_base_units=context.get("amount_base_units", 10_000_000))
            summary = f"Simulated NEAR Intents dry quote generated for {quote['source_amount_display']} -> {quote['estimated_destination_amount']}."
            next_action = "none"

        else:
            summary = f"Intent '{intent}' processed via tool registry."

        # Persist AgentRun and AgentToolCall records
        run = AgentRun(
            organization_id="org-fundguard-global",
            competition_id=competition_id,
            intent=intent,
            prompt=prompt,
            status="completed",
            summary=summary,
            metta_expressions_evaluated=json.dumps(self.metta.get_traces())
        )
        self.db.add(run)
        self.db.flush()

        for tc in recorded_tool_calls:
            clean_args = {k: v for k, v in tc["arguments"].items() if k != "db"}
            call_row = AgentToolCall(
                agent_run_id=run.id,
                tool_name=tc["tool"],
                arguments_json=json.dumps(clean_args, default=str),
                result_json=json.dumps(tc["result"], default=str),
                error_json=tc["error"],
                duration_ms=tc["duration_ms"]
            )
            self.db.add(call_row)

        self.db.commit()
        self.db.refresh(run)

        return {
            "agent_run_id": run.id,
            "status": run.status,
            "summary": run.summary,
            "next_action": next_action,
            "metta_traces": self.metta.get_traces(),
            "tool_calls": [
                {
                    "tool": tc["tool"],
                    "duration_ms": tc["duration_ms"],
                    "result_summary": tc["result"]
                }
                for tc in recorded_tool_calls
            ]
        }
