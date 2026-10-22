from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.agent.metta_engine import MeTTAEngine
from app.models import LearnedRule, Recipient, RecipientReliability
from app.services.audit import add_audit
from app.services.workflows import correlation_id


def record_reviewer_feedback(
    db: Session,
    recipient_id: str,
    outcome: str,
    reviewer: str,
    feedback_note: str = "",
    case_id: str | None = None,
    competition_id: str | None = None
) -> dict[str, Any]:
    engine = MeTTAEngine()

    rel = db.query(RecipientReliability).filter_by(recipient_id=recipient_id).first()
    if not rel:
        rel = RecipientReliability(
            recipient_id=recipient_id,
            score=1.0,
            successful_payouts=0,
            disputes_count=0,
            last_feedback=feedback_note,
            last_updated=datetime.now(UTC)
        )
        db.add(rel)
        db.flush()

    old_score = rel.score
    new_score = engine.calculate_updated_reliability(old_score, outcome)
    rel.score = round(new_score, 4)
    rel.last_feedback = feedback_note
    rel.last_updated = datetime.now(UTC)

    if outcome == "confirmed_settlement":
        rel.successful_payouts += 1
    elif outcome == "dispute_penalty":
        rel.disputes_count += 1

    # Record in audit trail
    add_audit(
        db,
        competition_id=competition_id,
        entity_type="recipient_reliability",
        entity_id=rel.id,
        action="learning.feedback_recorded",
        actor=reviewer,
        correlation_id=correlation_id(),
        details={
            "recipient_id": recipient_id,
            "outcome": outcome,
            "old_score": old_score,
            "new_score": rel.score,
            "note": feedback_note,
            "case_id": case_id
        }
    )
    db.commit()
    db.refresh(rel)

    return {
        "recipient_id": rel.recipient_id,
        "old_score": old_score,
        "new_score": rel.score,
        "successful_payouts": rel.successful_payouts,
        "disputes_count": rel.disputes_count,
        "last_feedback": rel.last_feedback,
        "last_updated": rel.last_updated.isoformat()
    }


def register_new_learned_rule(db: Session, payload) -> dict[str, Any]:
    rule = LearnedRule(
        competition_id=payload.competition_id,
        rule_name=payload.rule_name,
        rule_expression=payload.rule_expression,
        created_by=payload.created_by,
        rationale=payload.rationale,
        status="active"
    )
    db.add(rule)
    db.flush()

    # Load into MeTTA runtime engine
    engine = MeTTAEngine()
    engine.register_custom_rule(payload.rule_name, payload.rule_expression)

    add_audit(
        db,
        competition_id=payload.competition_id,
        entity_type="learned_rule",
        entity_id=rule.id,
        action="learning.rule_registered",
        actor=payload.created_by,
        correlation_id=correlation_id(),
        details={
            "rule_name": rule.rule_name,
            "expression": rule.rule_expression,
            "rationale": rule.rationale
        }
    )
    db.commit()
    db.refresh(rule)

    return {
        "id": rule.id,
        "rule_name": rule.rule_name,
        "rule_expression": rule.rule_expression,
        "created_by": rule.created_by,
        "rationale": rule.rationale,
        "status": rule.status,
        "created_at": rule.created_at.isoformat()
    }


def get_learning_insights(db: Session, competition_id: str | None = None) -> dict[str, Any]:
    rules_q = db.query(LearnedRule)
    if competition_id:
        rules_q = rules_q.filter((LearnedRule.competition_id == competition_id) | (LearnedRule.competition_id.is_(None)))
    active_rules = rules_q.order_by(LearnedRule.created_at.desc()).all()

    rel_records = db.query(RecipientReliability).all()
    recipient_scores = []
    for r in rel_records:
        rec = db.get(Recipient, r.recipient_id)
        display_name = rec.display_name if rec else r.recipient_id
        wallet = rec.wallet_address if rec else ""
        recipient_scores.append({
            "recipient_id": r.recipient_id,
            "display_name": display_name,
            "wallet_address": wallet,
            "reliability_score": r.score,
            "successful_payouts": r.successful_payouts,
            "disputes_count": r.disputes_count,
            "last_feedback": r.last_feedback,
            "last_updated": r.last_updated.isoformat()
        })

    avg_reliability = sum(r["reliability_score"] for r in recipient_scores) / len(recipient_scores) if recipient_scores else 1.0

    return {
        "competition_id": competition_id,
        "average_reliability_score": round(avg_reliability, 3),
        "total_active_learned_rules": len(active_rules),
        "active_learned_rules": [
            {
                "id": rule.id,
                "rule_name": rule.rule_name,
                "rule_expression": rule.rule_expression,
                "created_by": rule.created_by,
                "rationale": rule.rationale,
                "created_at": rule.created_at.isoformat()
            }
            for rule in active_rules
        ],
        "recipient_reliability_matrix": recipient_scores,
        "adaptation_status": "active_closed_loop_learning"
    }
