import json
import time

from sqlalchemy.orm import Session

from app.models import (
    AuditEvent,
    FundingPolicyVersion,
    Payout,
    PayoutBatch,
    Recipient,
    ReconciliationCase,
)
from app.services.audit import add_audit
from app.services.policy_engine import (
    calculate_proportional_allocation,
    compute_hash,
    default_policy_rules,
    validate_proposal,
)
from app.services.settlement import get_settlement_adapter
from app.services.stellar_service import (
    StellarTestnetService,
    simulate_near_intents_quote,
)


def tool_get_funding_policy(db: Session, competition_id: str) -> dict:
    """Tool: get_funding_policy. Retrieves active policy version and rules for a competition."""
    policy = db.query(FundingPolicyVersion).filter_by(competition_id=competition_id, status="active").order_by(FundingPolicyVersion.version.desc()).first()
    if not policy:
        # Create default canonical policy if none exists yet
        rules = default_policy_rules()
        rules_hash = compute_hash(rules)
        policy = FundingPolicyVersion(competition_id=competition_id, version=1, status="active",
                                      rules_json=json.dumps(rules), rules_hash=rules_hash, created_by="system")
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return {
        "policy_version_id": policy.id,
        "version": policy.version,
        "status": policy.status,
        "rules_hash": policy.rules_hash,
        "rules": json.loads(policy.rules_json)
    }

def tool_get_eligible_teams(db: Session, competition_id: str) -> dict:
    """Tool: get_eligible_teams. Retrieves only verified eligible recipients."""
    recipients = db.query(Recipient).filter_by(competition_id=competition_id, eligibility_status="verified").all()
    return {
        "competition_id": competition_id,
        "eligible_count": len(recipients),
        "teams": [
            {
                "id": r.id,
                "display_name": r.display_name,
                "wallet_address": r.wallet_address,
                "eligibility_status": r.eligibility_status
            }
            for r in recipients
        ]
    }

def tool_calculate_allocation(db: Session, competition_id: str, recipient_ids: list = None) -> dict:
    """Tool: calculate_allocation. Deterministically calculates funding release, awards, and reserve."""
    policy_data = tool_get_funding_policy(db, competition_id)
    rules = policy_data["rules"]
    if recipient_ids is not None:
        eligible_count = len(recipient_ids)
    else:
        eligible_teams = tool_get_eligible_teams(db, competition_id)
        eligible_count = eligible_teams["eligible_count"]

    calc = calculate_proportional_allocation(rules, eligible_count)
    return {
        "competition_id": competition_id,
        "policy_version_id": policy_data["policy_version_id"],
        "rules_hash": policy_data["rules_hash"],
        **calc
    }

def tool_validate_payout_batch(db: Session, batch_id: str) -> dict:
    """Tool: validate_payout_batch. Evaluates eligibility, caps, duplicates, and accounting."""
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        return {"error": "Batch not found", "valid": False}
    payouts = db.query(Payout).filter_by(batch_id=batch_id).all()
    recipients = []
    for p in payouts:
        r = db.get(Recipient, p.recipient_id)
        if r:
            recipients.append({
                "id": r.id,
                "display_name": r.display_name,
                "wallet_address": r.wallet_address,
                "eligibility_status": r.eligibility_status
            })

    policy_data = tool_get_funding_policy(db, batch.competition_id)
    per_recipient = payouts[0].amount_base_units if payouts else 0
    val = validate_proposal(recipients, per_recipient, batch.reserve_base_units, policy_data["rules"])
    return {
        "batch_id": batch.id,
        "content_hash": batch.content_hash,
        "status": batch.status,
        **val
    }

def tool_request_human_approval(db: Session, batch_id: str, content_hash: str) -> dict:
    """Tool: request_human_approval. Creates a review requirement; agent cannot approve on its own."""
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        return {"error": "Batch not found"}
    if batch.content_hash != content_hash:
        return {"error": "Provided hash does not match batch content hash", "action": "HALT"}

    return {
        "batch_id": batch.id,
        "status": "pending_approval",
        "action_required": "human_approval_required",
        "content_hash": batch.content_hash,
        "instruction": "An authorized finance reviewer must review the batch and approve the exact content hash."
    }

def tool_get_approval_status(db: Session, batch_id: str) -> dict:
    """Tool: get_approval_status. Returns current authorization status and approver identity."""
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        return {"error": "Batch not found"}
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "approved_by": batch.approved_by,
        "approved_at": batch.approved_at.isoformat() if batch.approved_at else None,
        "approval_hash": batch.approval_hash,
        "content_hash": batch.content_hash,
        "is_approved": batch.status == "approved" and batch.approval_hash == batch.content_hash
    }

def tool_execute_approved_payout(db: Session, batch_id: str, approved_hash: str,
                                 requested_by: str = "agent-orchestrator", mode: str = "simulated") -> dict:
    """Tool: execute_approved_payout. Revalidates approval hash and invokes settlement adapter."""
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        return {"error": "Batch not found"}
    if batch.status != "approved" or batch.approval_hash != approved_hash or batch.content_hash != approved_hash:
        return {
            "error": "Execution denied: batch is not approved for the exact requested hash.",
            "halted": True
        }

    adapter = get_settlement_adapter(mode)
    payouts = db.query(Payout).filter_by(batch_id=batch_id).all()
    results = []
    for p in payouts:
        if p.status in ("simulated", "confirmed"):
            results.append({"payout_id": p.id, "status": p.status, "tx_hash": p.tx_hash})
            continue
        recipient = db.get(Recipient, p.recipient_id)
        res = adapter.submit_and_verify(destination=recipient.wallet_address, amount_base_units=p.amount_base_units,
                                        asset_code=batch.asset_code)
        p.status = res.status
        p.tx_hash = res.tx_hash
        p.receipt_json = json.dumps(res.receipt, sort_keys=True)
        p.failure_reason = res.failure_reason
        results.append({"payout_id": p.id, "status": p.status, "tx_hash": p.tx_hash})

    batch.status = mode
    add_audit(db, competition_id=batch.competition_id, entity_type="payout_batch", entity_id=batch.id,
              action=f"batch.{mode}", actor=requested_by, correlation_id=f"agent-exec-{int(time.time())}",
              details={"payout_count": len(payouts), "mode": mode})
    db.commit()
    db.refresh(batch)
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "execution_mode": mode,
        "payouts": results
    }

def tool_verify_transaction(tx_hash: str, destination: str, expected_amount_base_units: int,
                            expected_asset: str = "XLM") -> dict:
    """Tool: verify_transaction. Independently queries Stellar testnet for payment proof."""
    svc = StellarTestnetService()
    return svc.verify_transaction_and_payment(tx_hash, destination, expected_amount_base_units, expected_asset)

def tool_reconcile_payout(db: Session, payout_id: str) -> dict:
    """Tool: reconcile_payout. Reconciles an unresolved payout against network records."""
    payout = db.get(Payout, payout_id)
    if not payout:
        return {"error": "Payout not found"}
    recipient = db.get(Recipient, payout.recipient_id)
    batch = db.get(PayoutBatch, payout.batch_id)

    if payout.status == "simulated":
        return {"payout_id": payout.id, "status": "simulated", "note": "Simulation receipt is final for local demo."}
    if payout.status == "confirmed":
        return {"payout_id": payout.id, "status": "confirmed", "tx_hash": payout.tx_hash}

    # Query network evidence if a tx_hash exists
    if payout.tx_hash:
        svc = StellarTestnetService()
        verification = svc.verify_transaction_and_payment(payout.tx_hash, recipient.wallet_address,
                                                          payout.amount_base_units, batch.asset_code)
        if verification.get("verified"):
            payout.status = "confirmed"
            db.commit()
            return {"payout_id": payout.id, "status": "confirmed", "verification": verification}

    # Check for open reconciliation case
    rc = db.query(ReconciliationCase).filter_by(payout_id=payout_id).first()
    return {
        "payout_id": payout.id,
        "status": payout.status,
        "reconciliation_case_status": rc.status if rc else "no_case_filed",
        "action": "manual_review_or_retry_required"
    }

def tool_get_audit_history(db: Session, competition_id: str = None, entity_id: str = None) -> list:
    """Tool: get_audit_history. Retrieves tamper-evident audit history."""
    q = db.query(AuditEvent)
    if competition_id:
        q = q.filter_by(competition_id=competition_id)
    if entity_id:
        q = q.filter_by(entity_id=entity_id)
    events = q.order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc()).all()
    return [
        {
            "id": e.id,
            "action": e.action,
            "actor": e.actor,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "created_at": e.created_at.isoformat(),
            "event_hash": e.event_hash
        }
        for e in events
    ]

def tool_get_simulated_near_quote(from_asset: str = "XLM", to_asset: str = "NEAR",
                                  amount_base_units: int = 10_000_000) -> dict:
    """Tool: get_simulated_near_quote. Returns simulated dry quote for NEAR Intents cross-chain leg."""
    return simulate_near_intents_quote(from_asset, to_asset, amount_base_units)
