import csv
import io
import json

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agent.evaluator import AgentEvaluator
from app.agent.metta_engine import MeTTAEngine
from app.agent.orchestrator import OmegaAgentOrchestrator
from app.database import get_db
from app.models import (
    Competition,
    FundingPolicyVersion,
    Organization,
    Payout,
    PayoutBatch,
    Recipient,
)
from app.schemas import (
    AgentRunRequest,
    ApprovalRequest,
    BatchCreate,
    BulkRecipientCreate,
    BulkRecipientItem,
    CompetitionCreate,
    ExecuteRequest,
    LearnedRuleCreate,
    LearningFeedbackRequest,
    NearQuoteRequest,
    OrganizationCreate,
    PolicySimulateRequest,
    PolicyVersionCreate,
    RecipientCreate,
    ReconciliationResolveRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.auth_service import authenticate_user, register_user
from app.services.audit import add_audit
from app.services.learning_service import (
    get_learning_insights,
    record_reviewer_feedback,
    register_new_learned_rule,
)
from app.services.policy_engine import (
    calculate_proportional_allocation,
    default_policy_rules,
    validate_proposal,
)
from app.services.reconciliation import (
    list_reconciliation_cases,
    resolve_reconciliation_case,
)
from app.services.stellar_service import (
    StellarTestnetService,
    fund_account_via_friendbot,
    generate_valid_testnet_keypair,
    simulate_near_intents_quote,
    validate_stellar_address,
)
from app.services.treasury import get_treasury_summary
from app.services.workflows import (
    approve_batch,
    audit_chain,
    cancel_batch,
    correlation_id,
    create_batch,
    create_competition,
    create_organization,
    create_policy_version,
    create_recipient,
    execute_batch,
    serialize_batch,
)

router = APIRouter()

# Health
@router.get("/health")
def health():
    return {"status": "ok", "service": "omega-fundguard-api"}

# Authentication
@router.post("/auth/register", status_code=201)
def post_register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, payload)

@router.post("/auth/login")
def post_login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    return authenticate_user(db, payload)

# Organizations
@router.get("/organizations")
def list_organizations(db: Session = Depends(get_db)):
    rows = db.query(Organization).all()
    if not rows:
        # Default org fallback
        default_org = Organization(id="org-basix-global", name="BASIX Market Hackathons", slug="basix-market")
        db.add(default_org)
        db.commit()
        db.refresh(default_org)
        rows = [default_org]
    return [{"id": o.id, "name": o.name, "slug": o.slug, "status": o.status, "created_at": o.created_at.isoformat()} for o in rows]

@router.post("/organizations", status_code=201)
def post_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    org = create_organization(db, payload)
    return {"id": org.id, "name": org.name, "slug": org.slug, "status": org.status, "created_at": org.created_at.isoformat()}

# Competitions
@router.get("/competitions")
def list_competitions(organization_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Competition)
    if organization_id:
        query = query.filter(Competition.organization_id == organization_id)
    rows = query.order_by(Competition.created_at.desc()).all()
    return [{"id": x.id, "name": x.name, "description": x.description, "status": x.status,
             "network": x.network, "default_currency": x.default_currency,
             "organization_id": x.organization_id,
             "created_at": x.created_at.isoformat()} for x in rows]

@router.post("/competitions", status_code=201)
def post_competition(payload: CompetitionCreate, db: Session = Depends(get_db)):
    org_id = payload.organization_id or "org-basix-global"
    row = create_competition(db, payload, organization_id=org_id)
    return {"id": row.id, "name": row.name, "description": row.description, "status": row.status,
             "network": row.network, "default_currency": row.default_currency,
             "organization_id": row.organization_id,
             "created_at": row.created_at.isoformat()}

@router.get("/competitions/{competition_id}")
def get_competition(competition_id: str, db: Session = Depends(get_db)):
    row = db.get(Competition, competition_id)
    if not row:
        raise HTTPException(404, "Competition not found")
    return {"id": row.id, "name": row.name, "description": row.description, "status": row.status,
            "network": row.network, "default_currency": row.default_currency,
            "created_at": row.created_at.isoformat()}

# Funding Policies
@router.get("/competitions/{competition_id}/policies")
def get_policies(competition_id: str, db: Session = Depends(get_db)):
    if not db.get(Competition, competition_id):
        raise HTTPException(404, "Competition not found")
    rows = db.query(FundingPolicyVersion).filter_by(competition_id=competition_id).order_by(FundingPolicyVersion.version.desc()).all()
    return [
        {
            "id": p.id,
            "version": p.version,
            "status": p.status,
            "rules_hash": p.rules_hash,
            "rules": json.loads(p.rules_json),
            "created_by": p.created_by,
            "created_at": p.created_at.isoformat()
        }
        for p in rows
    ]

@router.post("/competitions/{competition_id}/policies", status_code=201)
def post_policy(competition_id: str, payload: PolicyVersionCreate, db: Session = Depends(get_db)):
    pol = create_policy_version(db, competition_id, payload)
    return {
        "id": pol.id,
        "version": pol.version,
        "status": pol.status,
        "rules_hash": pol.rules_hash,
        "rules": json.loads(pol.rules_json),
        "created_at": pol.created_at.isoformat()
    }

@router.post("/competitions/{competition_id}/policies/simulate")
def simulate_policy(competition_id: str, payload: PolicySimulateRequest, db: Session = Depends(get_db)):
    rules = default_policy_rules(
        target_eligible_count=payload.target_eligible_count,
        total_fund_base_units=payload.total_fund_base_units
    )
    result = calculate_proportional_allocation(rules, payload.eligible_count)
    return {
        "simulation_parameters": payload.model_dump(),
        "calculated_outcome": result
    }

# Recipients
@router.get("/competitions/{competition_id}/recipients")
def list_recipients(competition_id: str, db: Session = Depends(get_db)):
    if not db.get(Competition, competition_id):
        raise HTTPException(404, "Competition not found")
    rows = db.query(Recipient).filter_by(competition_id=competition_id).order_by(Recipient.created_at.desc()).all()
    return [{"id": r.id, "competition_id": r.competition_id, "display_name": r.display_name,
             "wallet_address": r.wallet_address, "eligibility_status": r.eligibility_status,
             "eligibility_note": r.eligibility_note,
             "is_valid_strkey": validate_stellar_address(r.wallet_address),
             "created_at": r.created_at.isoformat()} for r in rows]

@router.post("/competitions/{competition_id}/recipients", status_code=201)
def post_recipient(competition_id: str, payload: RecipientCreate, db: Session = Depends(get_db)):
    r = create_recipient(db, competition_id, payload)
    return {"id": r.id, "competition_id": r.competition_id, "display_name": r.display_name,
            "wallet_address": r.wallet_address, "eligibility_status": r.eligibility_status,
            "eligibility_note": r.eligibility_note, "created_at": r.created_at.isoformat()}

@router.post("/competitions/{competition_id}/recipients/{recipient_id}/verify")
def verify_recipient(competition_id: str, recipient_id: str, reviewer: str = "Finance Reviewer", note: str = "Verified by reviewer", db: Session = Depends(get_db)):
    r = db.get(Recipient, recipient_id)
    if not r or r.competition_id != competition_id:
        raise HTTPException(404, "Recipient not found in competition")
    if r.eligibility_status != "pending":
        raise HTTPException(409, f"Only pending recipients can be verified; current status is {r.eligibility_status}")
    r.eligibility_status = "verified"
    r.eligibility_note = note
    add_audit(db, competition_id=competition_id, entity_type="recipient", entity_id=r.id,
              action="recipient.verified", actor=reviewer, correlation_id=correlation_id(),
              details={"reviewer": reviewer, "note": note})
    db.commit()
    db.refresh(r)
    return {"id": r.id, "eligibility_status": r.eligibility_status, "eligibility_note": r.eligibility_note}

@router.get("/competitions/{competition_id}/recipients/template.csv")
def get_recipients_template():
    csv_text = (
        "name,wallet_address,notes\n"
        "Alpha Pioneers,GA7SFOTHBSSRUGL4NUYZXCQTO2MDDJYUIEVPYIYPCYD2BR2RQOVNXIHD,Finalist recipient\n"
        "Beta Innovators,GB2GGSI4Q4JUC2K4HSCDYDK5XAZQD5DXTRC3COL4QZRHLZBSGDK4DPVW,Track award winner\n"
        "Gamma Protocol,GCRXSDVF23OPVXSXBUQJWQ3VMWGOX24YUGLB3CDBYOVV23CIAVTIPSJH,Grant cohort team\n"
    )
    return StreamingResponse(
        io.StringIO(csv_text),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=recipients_template.csv"}
    )

@router.post("/competitions/{competition_id}/recipients/bulk")
def post_recipients_bulk(competition_id: str, payload: BulkRecipientCreate, db: Session = Depends(get_db)):
    comp = db.get(Competition, competition_id)
    if not comp:
        raise HTTPException(404, "Competition not found")

    existing_recipients = db.query(Recipient).filter_by(competition_id=competition_id).all()
    existing_wallets = {r.wallet_address.strip() for r in existing_recipients}

    created = []
    errors = []
    seen_in_batch = set()

    for idx, item in enumerate(payload.recipients):
        row_num = idx + 1
        name = (item.display_name or "").strip()
        wallet = (item.wallet_address or "").strip()
        note = (item.eligibility_note or "").strip()

        if not name:
            errors.append({"row": row_num, "name": name, "wallet": wallet, "error": "Display name is required"})
            continue

        if not wallet:
            errors.append({"row": row_num, "name": name, "wallet": wallet, "error": "Wallet address is required"})
            continue

        if not validate_stellar_address(wallet):
            errors.append({"row": row_num, "name": name, "wallet": wallet, "error": "Invalid Stellar ed25519 public address (must start with 'G' and be 56 characters)"})
            continue

        if wallet in existing_wallets:
            errors.append({"row": row_num, "name": name, "wallet": wallet, "error": "Wallet address is already registered in this workspace"})
            continue

        if wallet in seen_in_batch:
            errors.append({"row": row_num, "name": name, "wallet": wallet, "error": "Duplicate wallet address within this import batch"})
            continue

        seen_in_batch.add(wallet)
        existing_wallets.add(wallet)

        initial_note = note or ("Bulk imported recipient" if not payload.auto_verify else f"Verified via bulk import by {payload.reviewer}")
        row = Recipient(
            competition_id=competition_id,
            organization_id=comp.organization_id,
            display_name=name,
            wallet_address=wallet,
            eligibility_status="pending",
            eligibility_note=initial_note,
            evidence_json=json.dumps(item.evidence or {"source": "bulk_import"})
        )
        db.add(row)
        db.flush()

        add_audit(
            db,
            competition_id=competition_id,
            entity_type="recipient",
            entity_id=row.id,
            action="recipient.created",
            actor=payload.created_by,
            correlation_id=correlation_id(),
            details={"display_name": row.display_name, "eligibility_status": "pending", "source": "bulk_import"}
        )

        if payload.auto_verify:
            row.eligibility_status = "verified"
            add_audit(
                db,
                competition_id=competition_id,
                entity_type="recipient",
                entity_id=row.id,
                action="recipient.verified",
                actor=payload.reviewer,
                correlation_id=correlation_id(),
                details={"reviewer": payload.reviewer, "note": row.eligibility_note}
            )

        created.append(row)

    if created:
        add_audit(
            db,
            competition_id=competition_id,
            entity_type="competition",
            entity_id=competition_id,
            action="recipients.bulk_imported",
            actor=payload.created_by,
            correlation_id=correlation_id(),
            details={"imported_count": len(created), "skipped_count": len(errors), "auto_verified": payload.auto_verify}
        )
        db.commit()
    elif not errors:
        db.commit()

    return {
        "total": len(payload.recipients),
        "imported_count": len(created),
        "skipped_count": len(errors),
        "recipients": [{
            "id": r.id,
            "competition_id": r.competition_id,
            "display_name": r.display_name,
            "wallet_address": r.wallet_address,
            "eligibility_status": r.eligibility_status,
            "eligibility_note": r.eligibility_note,
            "is_valid_strkey": True,
            "created_at": r.created_at.isoformat()
        } for r in created],
        "errors": errors
    }

@router.post("/competitions/{competition_id}/recipients/upload-csv")
async def post_recipients_upload_csv(
    competition_id: str,
    file: UploadFile = File(...),
    auto_verify: bool = Form(default=False),
    reviewer: str = Form(default="CSV Import Reviewer"),
    created_by: str = Form(default="Administrator"),
    db: Session = Depends(get_db)
):
    comp = db.get(Competition, competition_id)
    if not comp:
        raise HTTPException(404, "Competition not found")

    content_bytes = await file.read()
    try:
        text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content_bytes.decode("latin-1")
        except Exception as e:
            raise HTTPException(422, f"Could not decode CSV file: {str(e)}")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise HTTPException(422, "The uploaded CSV file is empty.")

    first_row = [str(c).strip().lower().replace(" ", "_") for c in rows[0]]
    has_header = False
    name_col = -1
    wallet_col = -1
    note_col = -1

    for idx, col in enumerate(first_row):
        if col in ("name", "display_name", "team", "team_name", "recipient", "recipient_name"):
            name_col = idx
            has_header = True
        elif col in ("wallet", "wallet_address", "address", "stellar_address", "public_key", "key", "strkey"):
            wallet_col = idx
            has_header = True
        elif col in ("notes", "note", "eligibility_note", "review_note", "comments", "description"):
            note_col = idx
            has_header = True

    data_rows = rows[1:] if has_header else rows
    if not has_header:
        name_col = 0
        wallet_col = 1 if len(rows[0]) > 1 else -1
        note_col = 2 if len(rows[0]) > 2 else -1

    if wallet_col == -1:
        wallet_col = 1

    items = []
    for r in data_rows:
        if not r or all(not str(c).strip() for c in r):
            continue
        d_name = str(r[name_col]).strip() if 0 <= name_col < len(r) else ""
        d_wallet = str(r[wallet_col]).strip() if 0 <= wallet_col < len(r) else ""
        d_note = str(r[note_col]).strip() if 0 <= note_col < len(r) else ""
        items.append(BulkRecipientItem(display_name=d_name, wallet_address=d_wallet, eligibility_note=d_note))

    bulk_payload = BulkRecipientCreate(
        recipients=items,
        auto_verify=auto_verify,
        reviewer=reviewer,
        created_by=created_by
    )
    return post_recipients_bulk(competition_id, bulk_payload, db)

# Batches
@router.post("/competitions/{competition_id}/batches", status_code=201)
def post_batch(competition_id: str, payload: BatchCreate, idempotency_key: str = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db)):
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key header is required")
    batch = create_batch(db, competition_id, payload, idempotency_key)
    return serialize_batch(batch, db)

@router.get("/competitions/{competition_id}/batches")
def list_batches(competition_id: str, db: Session = Depends(get_db)):
    if not db.get(Competition, competition_id):
        raise HTTPException(404, "Competition not found")
    rows = db.query(PayoutBatch).filter_by(competition_id=competition_id).order_by(PayoutBatch.created_at.desc()).all()
    return [serialize_batch(row, db) for row in rows]

@router.get("/batches/{batch_id}")
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    return serialize_batch(batch, db)

@router.post("/batches/{batch_id}/validate")
def validate_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    payouts = db.query(Payout).filter_by(batch_id=batch_id).all()
    recipients = []
    for p in payouts:
        r = db.get(Recipient, p.recipient_id)
        if r:
            recipients.append({"id": r.id, "display_name": r.display_name, "wallet_address": r.wallet_address, "eligibility_status": r.eligibility_status})
    policy = db.query(FundingPolicyVersion).filter_by(competition_id=batch.competition_id, status="active").first()
    rules = json.loads(policy.rules_json) if policy else default_policy_rules()
    per_recipient = payouts[0].amount_base_units if payouts else 0
    val = validate_proposal(recipients, per_recipient, batch.reserve_base_units, rules)
    return {
        "batch_id": batch.id,
        "content_hash": batch.content_hash,
        "status": batch.status,
        **val
    }

@router.post("/batches/{batch_id}/approve")
def post_approval(batch_id: str, payload: ApprovalRequest, db: Session = Depends(get_db)):
    batch = approve_batch(db, batch_id, payload)
    return serialize_batch(batch, db)

@router.post("/batches/{batch_id}/execute")
def post_execution(batch_id: str, payload: ExecuteRequest, db: Session = Depends(get_db)):
    batch = execute_batch(db, batch_id, payload)
    return serialize_batch(batch, db)

@router.post("/batches/{batch_id}/cancel")
def post_cancel(batch_id: str, actor: str = "Finance Manager", db: Session = Depends(get_db)):
    batch = cancel_batch(db, batch_id, actor=actor)
    return serialize_batch(batch, db)

# Payouts
@router.get("/payouts/{payout_id}")
def get_payout(payout_id: str, db: Session = Depends(get_db)):
    p = db.get(Payout, payout_id)
    if not p:
        raise HTTPException(404, "Payout not found")
    recipient = db.get(Recipient, p.recipient_id)
    return {
        "id": p.id,
        "batch_id": p.batch_id,
        "recipient": {"id": recipient.id, "display_name": recipient.display_name, "wallet_address": recipient.wallet_address} if recipient else None,
        "amount_base_units": str(p.amount_base_units),
        "status": p.status,
        "tx_hash": p.tx_hash,
        "receipt": json.loads(p.receipt_json) if p.receipt_json else None,
        "failure_reason": p.failure_reason,
        "created_at": p.created_at.isoformat()
    }

@router.post("/payouts/{payout_id}/reconcile")
def reconcile_payout_route(payout_id: str, db: Session = Depends(get_db)):
    from app.agent.tools import tool_reconcile_payout
    return tool_reconcile_payout(db, payout_id)

# Treasury & Reconciliation
@router.get("/treasury/{competition_id}")
def treasury_summary_route(competition_id: str, db: Session = Depends(get_db)):
    if not db.get(Competition, competition_id):
        raise HTTPException(404, "Competition not found")
    return get_treasury_summary(db, competition_id)

@router.get("/reconciliation/cases")
def list_cases_route(competition_id: str = None, db: Session = Depends(get_db)):
    return list_reconciliation_cases(db, competition_id)

@router.post("/reconciliation/cases/{case_id}/resolve")
def resolve_case_route(case_id: str, payload: ReconciliationResolveRequest, db: Session = Depends(get_db)):
    return resolve_reconciliation_case(db, case_id, payload.decision, payload.reviewer, payload.resolution_note)

# Omega Agent & MeTTa
@router.post("/agent/run")
def run_agent_route(payload: AgentRunRequest, competition_id: str = Query(...), db: Session = Depends(get_db)):
    orch = OmegaAgentOrchestrator(db)
    return orch.run_agent_workflow(competition_id=competition_id, intent=payload.intent,
                                   prompt=payload.prompt, context=payload.context)

@router.get("/agent/eval")
def evaluate_agent_route(competition_id: str = Query(...), db: Session = Depends(get_db)):
    evaluator = AgentEvaluator(db)
    return evaluator.run_all_evaluations(competition_id=competition_id)

@router.post("/agent/metta")
def query_metta_route(query_str: str = Query(..., alias="q")):
    engine = MeTTAEngine()
    result = engine.query(query_str)
    return {"query": query_str, "result": result, "traces": engine.get_traces()}

# Closed-Loop Learning & Dynamic Rules ("The Agent That Grows Up")
@router.get("/agent/learning/insights")
def get_learning_insights_route(competition_id: str = None, db: Session = Depends(get_db)):
    return get_learning_insights(db, competition_id)

@router.post("/agent/learning/rules")
def register_learned_rule_route(payload: LearnedRuleCreate, db: Session = Depends(get_db)):
    return register_new_learned_rule(db, payload)

@router.post("/agent/learning/feedback")
def record_learning_feedback_route(payload: LearningFeedbackRequest, competition_id: str = None, db: Session = Depends(get_db)):
    return record_reviewer_feedback(
        db,
        recipient_id=payload.recipient_id,
        outcome=payload.outcome,
        reviewer=payload.reviewer,
        feedback_note=payload.feedback_note,
        case_id=payload.case_id,
        competition_id=competition_id
    )

# Stellar Testnet Operations & Independent Verification
@router.get("/stellar/custody")
def get_stellar_custody_route():
    svc = StellarTestnetService()
    return svc.get_account_balance()

@router.post("/stellar/fund-friendbot")
def fund_friendbot_route(public_key: str = Query(None)):
    return fund_account_via_friendbot(public_key)

@router.post("/stellar/generate-keypair")
def generate_keypair_route(fund_via_friendbot: bool = Query(False)):
    return generate_valid_testnet_keypair(fund_with_friendbot=fund_via_friendbot)

@router.post("/stellar/verify-tx")
def verify_stellar_tx_route(tx_hash: str = Query(...), destination: str = Query(...),
                            amount_base_units: int = Query(...), asset_code: str = Query("XLM")):
    svc = StellarTestnetService()
    return svc.verify_transaction_and_payment(
        tx_hash=tx_hash,
        expected_destination=destination,
        expected_amount_base_units=amount_base_units,
        expected_asset_code=asset_code
    )

# NEAR Intents Cross-Chain Simulator
@router.get("/near-intents/quote")
@router.post("/near-intents/quote")
def near_quote_route(payload: NearQuoteRequest = None, from_asset: str = "XLM", to_asset: str = "NEAR",
                     amount_base_units: int = 10_000_000):
    if payload:
        return simulate_near_intents_quote(payload.from_asset, payload.to_asset, payload.amount_base_units)
    return simulate_near_intents_quote(from_asset, to_asset, amount_base_units)

# Audit
@router.get("/audit/events")
def get_audit_events(competition_id: str = None, db: Session = Depends(get_db)):
    return audit_chain(db, competition_id)

@router.get("/audit/verify")
def verify_audit_events(competition_id: str = None, db: Session = Depends(get_db)):
    events = audit_chain(db, competition_id)
    return {"valid": all(e["integrity_valid"] for e in events), "event_count": len(events),
            "invalid_event_ids": [e["id"] for e in events if not e["integrity_valid"]]}

@router.get("/audit/export")
def export_audit_events(format: str = "json", competition_id: str = None, db: Session = Depends(get_db)):
    events = audit_chain(db, competition_id)
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "created_at", "action", "actor", "entity_type", "entity_id", "integrity_valid", "event_hash"])
        for e in events:
            writer.writerow([e["id"], e["created_at"], e["action"], e["actor"], e["entity_type"], e["entity_id"], e["integrity_valid"], e["event_hash"]])
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=fundguard_audit.csv"})
    return events
