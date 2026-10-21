import hashlib
import json

from app.models import AuditEvent


def add_audit(db, *, competition_id, entity_type, entity_id, action, actor, correlation_id, details):
    q = db.query(AuditEvent)
    if competition_id:
        q = q.filter_by(competition_id=competition_id)
    last = q.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).first()
    previous_hash = last.event_hash if last else None
    body = {
        "competition_id": competition_id, "entity_type": entity_type, "entity_id": entity_id,
        "action": action, "actor": actor, "correlation_id": correlation_id,
        "details": details, "previous_event_hash": previous_hash
    }
    event_hash = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    event = AuditEvent(
        competition_id=competition_id, entity_type=entity_type, entity_id=entity_id,
        action=action, actor=actor, correlation_id=correlation_id,
        details_json=json.dumps(details, sort_keys=True), previous_event_hash=previous_hash,
        event_hash=event_hash
    )
    db.add(event)
    return event
