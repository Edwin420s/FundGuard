import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Payout, PayoutBatch, Recipient, ReconciliationCase
from app.services.audit import add_audit


def create_or_get_reconciliation_case(db: Session, payout_id: str, reason: str) -> ReconciliationCase:
    payout = db.get(Payout, payout_id)
    if not payout:
        raise ValueError("Payout not found")
    case = db.query(ReconciliationCase).filter_by(payout_id=payout_id).first()
    if not case:
        case = ReconciliationCase(
            payout_id=payout_id,
            batch_id=payout.batch_id,
            status="open",
            evidence_json=json.dumps({"reason": reason, "created_at": datetime.now(UTC).isoformat()}),
            resolution_note=""
        )
        db.add(case)
        db.commit()
        db.refresh(case)
    return case

def list_reconciliation_cases(db: Session, competition_id: str = None) -> list:
    q = db.query(ReconciliationCase)
    if competition_id:
        batch_ids = [b.id for b in db.query(PayoutBatch).filter_by(competition_id=competition_id).all()]
        if not batch_ids:
            return []
        q = q.filter(ReconciliationCase.batch_id.in_(batch_ids))
    cases = q.order_by(ReconciliationCase.created_at.desc()).all()
    out = []
    for c in cases:
        payout = db.get(Payout, c.payout_id)
        recipient = db.get(Recipient, payout.recipient_id) if payout else None
        out.append({
            "id": c.id,
            "payout_id": c.payout_id,
            "batch_id": c.batch_id,
            "status": c.status,
            "recipient_name": recipient.display_name if recipient else "Unknown",
            "wallet_address": recipient.wallet_address if recipient else "Unknown",
            "amount_base_units": payout.amount_base_units if payout else 0,
            "resolution_note": c.resolution_note,
            "resolved_by": c.resolved_by,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            "evidence": json.loads(c.evidence_json) if c.evidence_json else {},
            "created_at": c.created_at.isoformat()
        })
    return out

def resolve_reconciliation_case(db: Session, case_id: str, decision: str, reviewer: str,
                                resolution_note: str) -> dict:
    case = db.get(ReconciliationCase, case_id)
    if not case:
        raise ValueError("Reconciliation case not found")
    payout = db.get(Payout, case.payout_id)
    batch = db.get(PayoutBatch, payout.batch_id) if payout else None

    case.resolved_by = reviewer
    case.resolved_at = datetime.now(UTC)
    case.resolution_note = resolution_note

    if decision == "confirm":
        case.status = "resolved_confirmed"
        if payout:
            payout.status = "confirmed"
    elif decision == "fail":
        case.status = "resolved_failed"
        if payout:
            payout.status = "failed"
            payout.failure_reason = resolution_note
    else:
        case.status = "investigating"

    if batch:
        add_audit(db, competition_id=batch.competition_id, entity_type="reconciliation_case",
                  entity_id=case.id, action=f"reconciliation.{decision}", actor=reviewer,
                  correlation_id=f"rec-res-{case.id[:8]}",
                  details={"decision": decision, "note": resolution_note, "payout_id": case.payout_id})

    db.commit()
    db.refresh(case)
    return {
        "case_id": case.id,
        "status": case.status,
        "decision": decision,
        "resolved_by": case.resolved_by,
        "resolved_at": case.resolved_at.isoformat()
    }
