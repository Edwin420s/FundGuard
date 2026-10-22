import hashlib
import json
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Approval,
    AuditEvent,
    Competition,
    FundingPolicyVersion,
    Organization,
    PaymentReceipt,
    Payout,
    PayoutBatch,
    Recipient,
    TreasuryReservation,
)
from app.services.audit import add_audit
from app.services.policy_engine import (
    compute_hash,
    default_policy_rules,
)
from app.services.settlement import get_settlement_adapter


def correlation_id():
    return str(uuid.uuid4())

def batch_payload(competition_id, recipient_amounts, asset_code, reserve):
    return {
        "competition_id": competition_id,
        "asset": {"type": "native", "code": asset_code, "network": "stellar-testnet"},
        "recipients": sorted(recipient_amounts, key=lambda x: x["recipient_id"]),
        "reserve_base_units": reserve,
    }

def create_organization(db: Session, payload):
    org = Organization(name=payload.name, slug=payload.slug)
    db.add(org)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An organization with this slug already exists")
    add_audit(db, competition_id=None, entity_type="organization", entity_id=org.id,
              action="organization.created", actor="admin", correlation_id=correlation_id(),
              details={"name": org.name, "slug": org.slug})
    db.commit()
    db.refresh(org)
    return org

def create_competition(db: Session, payload, organization_id: str = "org-basix-global"):
    row = Competition(name=payload.name, description=payload.description,
                      network=payload.network, organization_id=organization_id,
                      default_currency=payload.default_currency)
    db.add(row)
    db.flush()

    # Automatically initialize default version 1 funding policy for this competition
    rules = default_policy_rules()
    rules_hash = compute_hash(rules)
    policy = FundingPolicyVersion(competition_id=row.id, organization_id=organization_id,
                                  version=1, status="active", rules_json=json.dumps(rules),
                                  rules_hash=rules_hash, created_by="system")
    db.add(policy)

    actor = getattr(payload, "created_by", None) or "Administrator"
    add_audit(db, competition_id=row.id, entity_type="competition", entity_id=row.id, action="competition.created",
              actor=actor, correlation_id=correlation_id(),
              details={"name": row.name, "network": row.network, "initial_policy_hash": rules_hash})
    db.commit()
    db.refresh(row)
    return row

def create_policy_version(db: Session, competition_id: str, payload):
    comp = db.get(Competition, competition_id)
    if not comp:
        raise HTTPException(404, "Competition not found")
    latest = db.query(FundingPolicyVersion).filter_by(competition_id=competition_id).order_by(FundingPolicyVersion.version.desc()).first()
    next_version = (latest.version + 1) if latest else 1

    rules = default_policy_rules(
        target_eligible_count=payload.target_eligible_count,
        total_fund_base_units=payload.total_fund_base_units,
        currency=payload.currency,
        illustrative_fiat_usd=payload.illustrative_fiat_usd
    )
    rules_hash = compute_hash(rules)

    if latest:
        latest.status = "superseded"

    new_policy = FundingPolicyVersion(
        competition_id=competition_id,
        organization_id=comp.organization_id,
        version=next_version,
        status="active",
        rules_json=json.dumps(rules),
        rules_hash=rules_hash,
        created_by="organizer"
    )
    db.add(new_policy)
    add_audit(db, competition_id=competition_id, entity_type="funding_policy_version", entity_id=new_policy.id,
              action="policy.created", actor="organizer", correlation_id=correlation_id(),
              details={"version": next_version, "rules_hash": rules_hash, "rules": rules})
    db.commit()
    db.refresh(new_policy)
    return new_policy

def create_recipient(db: Session, competition_id: str, payload):
    competition = db.get(Competition, competition_id)
    if not competition:
        raise HTTPException(404, "Competition not found")
    if not payload.wallet_address.strip():
        raise HTTPException(422, "Wallet address is required")
    if payload.eligibility_status == "verified":
        raise HTTPException(422, "Recipients cannot self-assert verified eligibility; create as pending and use the review workflow.")

    row = Recipient(competition_id=competition_id, organization_id=competition.organization_id,
                    display_name=payload.display_name, wallet_address=payload.wallet_address.strip(),
                    eligibility_status=payload.eligibility_status, eligibility_note=payload.eligibility_note,
                    evidence_json=json.dumps(payload.evidence))
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A recipient with this wallet is already registered for this competition")
    actor = getattr(payload, "created_by", None) or "Administrator"
    add_audit(db, competition_id=competition_id, entity_type="recipient", entity_id=row.id,
              action="recipient.created", actor=actor, correlation_id=correlation_id(),
              details={"display_name": row.display_name, "eligibility_status": row.eligibility_status})
    db.commit()
    db.refresh(row)
    return row

def create_batch(db: Session, competition_id: str, payload, idempotency_key: str):
    if not idempotency_key or len(idempotency_key) > 160:
        raise HTTPException(400, "A valid Idempotency-Key header is required")
    competition = db.get(Competition, competition_id)
    if not competition:
        raise HTTPException(404, "Competition not found")
    existing = db.query(PayoutBatch).filter_by(competition_id=competition_id, idempotency_key=idempotency_key).first()
    if existing:
        return existing

    policy = db.query(FundingPolicyVersion).filter_by(competition_id=competition_id, status="active").order_by(FundingPolicyVersion.version.desc()).first()
    policy_version_id = policy.id if policy else None

    recipients = []
    for rid in payload.recipient_ids:
        recipient = db.get(Recipient, rid)
        if not recipient or recipient.competition_id != competition_id:
            raise HTTPException(422, f"Recipient {rid} is not part of this competition")
        if recipient.eligibility_status != "verified":
            raise HTTPException(422, f"Recipient {recipient.display_name} is not verified eligible")
        recipients.append(recipient)

    per_recipient = payload.amount_base_units
    amounts = [{"recipient_id": r.id, "amount_base_units": per_recipient} for r in recipients]
    canonical = batch_payload(competition_id, amounts, payload.asset_code, payload.reserve_base_units)
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    batch = PayoutBatch(
        competition_id=competition_id,
        organization_id=competition.organization_id,
        policy_version_id=policy_version_id,
        status="proposed",
        asset_code=payload.asset_code,
        asset_type=payload.asset_type,
        total_base_units=per_recipient * len(recipients),
        reserve_base_units=payload.reserve_base_units,
        content_hash=f"sha256:{digest}",
        idempotency_key=idempotency_key,
        execution_mode="simulated"
    )
    db.add(batch)
    db.flush()

    for recipient in recipients:
        db.add(Payout(batch_id=batch.id, recipient_id=recipient.id, amount_base_units=per_recipient, status="proposed"))

    # Create treasury reservation
    reservation = TreasuryReservation(
        competition_id=competition_id,
        batch_id=batch.id,
        asset_code=payload.asset_code,
        reserved_base_units=batch.total_base_units,
        status="active"
    )
    db.add(reservation)

    actor = getattr(payload, "created_by", None) or "Administrator"
    add_audit(db, competition_id=competition_id, entity_type="payout_batch", entity_id=batch.id,
              action="batch.proposed", actor=actor, correlation_id=correlation_id(),
              details={"content_hash": batch.content_hash, "payout_count": len(recipients),
                       "total_base_units": batch.total_base_units, "reserve_base_units": batch.reserve_base_units})
    db.commit()
    db.refresh(batch)
    return batch

def approve_batch(db: Session, batch_id: str, payload):
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    if batch.status != "proposed":
        raise HTTPException(409, f"Only proposed batches can be approved; current status is {batch.status}")
    if payload.confirm_hash != batch.content_hash:
        raise HTTPException(409, "Approval hash does not match the current batch content hash")

    approval_record = Approval(
        batch_id=batch.id,
        approver=payload.approver,
        role=payload.role,
        decision=payload.decision,
        approved_content_hash=payload.confirm_hash,
        reason=payload.reason
    )
    db.add(approval_record)

    if payload.decision == "approved":
        batch.status = "approved"
        batch.approved_by = payload.approver
        batch.approved_at = datetime.now(UTC)
        batch.approval_hash = batch.content_hash
        payouts = db.query(Payout).filter_by(batch_id=batch.id).all()
        for p in payouts:
            if p.status == "proposed":
                p.status = "authorized"
        action_name = "batch.approved"
    elif payload.decision == "rejected":
        batch.status = "cancelled"
        action_name = "batch.rejected"
    else:
        batch.status = "amendment_requested"
        action_name = "batch.amendment_requested"

    add_audit(db, competition_id=batch.competition_id, entity_type="payout_batch", entity_id=batch.id,
              action=action_name, actor=payload.approver, correlation_id=correlation_id(),
              details={"decision": payload.decision, "approval_hash": batch.approval_hash, "reason": payload.reason})
    db.commit()
    db.refresh(batch)
    return batch

def cancel_batch(db: Session, batch_id: str, actor: str = "Finance Manager"):
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    if batch.status in ("confirmed", "simulated"):
        raise HTTPException(409, "Cannot cancel an already settled/executed batch")
    batch.status = "cancelled"
    payouts = db.query(Payout).filter_by(batch_id=batch.id).all()
    for p in payouts:
        if p.status in ("proposed", "authorized"):
            p.status = "cancelled"
    add_audit(db, competition_id=batch.competition_id, entity_type="payout_batch", entity_id=batch.id,
              action="batch.cancelled", actor=actor, correlation_id=correlation_id(),
              details={"batch_id": batch.id})
    db.commit()
    db.refresh(batch)
    return batch

def execute_batch(db: Session, batch_id: str, payload):
    batch = db.get(PayoutBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    if batch.status != "approved" or not batch.approval_hash or batch.approval_hash != batch.content_hash:
        raise HTTPException(409, "Batch must be approved for its exact current content hash before execution")

    mode = payload.mode
    batch.execution_mode = mode
    adapter = get_settlement_adapter(mode)

    payouts = db.query(Payout).filter_by(batch_id=batch_id).all()
    confirmed_count = 0
    simulated_count = 0
    unresolved_count = 0
    failed_count = 0

    for payout in payouts:
        if payout.status in ("simulated", "confirmed"):
            continue
        if payout.status not in ("proposed", "authorized"):
            raise HTTPException(409, f"Payout {payout.id} has status {payout.status}; reconcile before retry")
        recipient = db.get(Recipient, payout.recipient_id)

        result = adapter.submit_and_verify(
            destination=recipient.wallet_address,
            amount_base_units=payout.amount_base_units,
            asset_code=batch.asset_code
        )
        payout.status = result.status
        payout.tx_hash = result.tx_hash
        payout.receipt_json = json.dumps(result.receipt, sort_keys=True)
        payout.failure_reason = result.failure_reason

        if result.status == "confirmed":
            confirmed_count += 1
            # Record verified receipt row
            rc = PaymentReceipt(
                payout_id=payout.id,
                tx_hash=result.tx_hash or "TESTNET_RECEIPT",
                ledger=result.ledger,
                operation_index=0,
                source_account="stellar-testnet-custody",
                destination=recipient.wallet_address,
                asset_code=batch.asset_code,
                asset_type="native",
                amount_base_units=payout.amount_base_units,
                verified_at=datetime.now(UTC),
                verification_status="independently_verified"
            )
            db.add(rc)
            try:
                from app.services.learning_service import record_reviewer_feedback
                record_reviewer_feedback(db, recipient.id, "confirmed_settlement", "settlement-system",
                                         "Independently verified on Stellar testnet", competition_id=batch.competition_id)
            except Exception:
                pass
        elif result.status == "simulated":
            simulated_count += 1
            try:
                from app.services.learning_service import record_reviewer_feedback
                record_reviewer_feedback(db, recipient.id, "confirmed_settlement", "settlement-system",
                                         "Executed simulated payout batch", competition_id=batch.competition_id)
            except Exception:
                pass
        elif result.status == "unresolved":
            unresolved_count += 1
            try:
                from app.services.learning_service import record_reviewer_feedback
                record_reviewer_feedback(db, recipient.id, "dispute_penalty", "settlement-system",
                                         "Unresolved payout requires reconciliation", competition_id=batch.competition_id)
            except Exception:
                pass
        else:
            failed_count += 1

    # Derive overall batch status from child payout states
    if unresolved_count > 0:
        batch.status = "unresolved"
    elif failed_count > 0 and confirmed_count > 0:
        batch.status = "partially_confirmed"
    elif failed_count > 0 and confirmed_count == 0:
        batch.status = "failed"
    elif confirmed_count > 0 and confirmed_count == len(payouts):
        batch.status = "confirmed"
    elif simulated_count > 0:
        batch.status = "simulated"
    else:
        batch.status = mode

    add_audit(db, competition_id=batch.competition_id, entity_type="payout_batch", entity_id=batch.id,
              action=f"batch.{batch.status}", actor=payload.requested_by, correlation_id=correlation_id(),
              details={"payout_count": len(payouts), "mode": mode, "status": batch.status,
                       "confirmed": confirmed_count, "simulated": simulated_count, "unresolved": unresolved_count})
    db.commit()
    db.refresh(batch)
    return batch

def serialize_batch(batch: PayoutBatch, db: Session):
    payouts = db.query(Payout).filter_by(batch_id=batch.id).all()
    approvals = db.query(Approval).filter_by(batch_id=batch.id).all()
    return {
        "id": batch.id, "competition_id": batch.competition_id, "status": batch.status,
        "policy_version_id": batch.policy_version_id,
        "asset": {"type": batch.asset_type, "code": batch.asset_code, "network": "stellar-testnet"},
        "total_base_units": str(batch.total_base_units), "reserve_base_units": str(batch.reserve_base_units),
        "content_hash": batch.content_hash, "approved_by": batch.approved_by,
        "approved_at": batch.approved_at.isoformat() if batch.approved_at else None,
        "approval_hash": batch.approval_hash, "execution_mode": batch.execution_mode,
        "created_at": batch.created_at.isoformat(),
        "approvals": [
            {
                "id": a.id, "approver": a.approver, "role": a.role, "decision": a.decision,
                "created_at": a.created_at.isoformat(), "reason": a.reason
            }
            for a in approvals
        ],
        "payouts": [{
            "id": p.id, "recipient_id": p.recipient_id, "amount_base_units": str(p.amount_base_units),
            "status": p.status, "tx_hash": p.tx_hash, "receipt": json.loads(p.receipt_json) if p.receipt_json else None,
            "failure_reason": p.failure_reason
        } for p in payouts]
    }

def audit_chain(db: Session, competition_id: str = None):
    q = db.query(AuditEvent)
    if competition_id:
        q = q.filter_by(competition_id=competition_id)
    events = q.order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc()).all()
    results = []
    previous = None
    for event in events:
        body = {"competition_id": event.competition_id, "entity_type": event.entity_type,
                "entity_id": event.entity_id, "action": event.action, "actor": event.actor,
                "correlation_id": event.correlation_id, "details": json.loads(event.details_json),
                "previous_event_hash": event.previous_event_hash}
        expected = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        valid = expected == event.event_hash and event.previous_event_hash == previous
        results.append({"id": event.id, "competition_id": event.competition_id,
                        "action": event.action, "entity_type": event.entity_type,
                        "entity_id": event.entity_id, "actor": event.actor, "correlation_id": event.correlation_id,
                        "created_at": event.created_at.isoformat(), "event_hash": event.event_hash,
                        "previous_event_hash": event.previous_event_hash, "integrity_valid": valid,
                        "details": json.loads(event.details_json)})
        previous = event.event_hash
    return results
