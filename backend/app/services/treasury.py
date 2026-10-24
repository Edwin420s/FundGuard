import json

from sqlalchemy.orm import Session

from app.models import (
    FundingPolicyVersion,
    Payout,
    PayoutBatch,
    Recipient,
)
from app.services.policy_engine import (
    calculate_proportional_allocation,
    default_policy_rules,
)


def get_treasury_summary(db: Session, competition_id: str) -> dict:
    """
    Computes real-time treasury accounting breakdown:
    - total_fund_base_units
    - allocated_base_units (proposed + approved)
    - reserved_base_units (approved + in-flight)
    - paid_base_units (confirmed / simulated)
    - unresolved_base_units (in reconciliation)
    - carry_forward_reserve_base_units
    - available_base_units
    """
    policy = db.query(FundingPolicyVersion).filter_by(competition_id=competition_id, status="active").order_by(FundingPolicyVersion.version.desc()).first()
    if policy:
        rules = json.loads(policy.rules_json)
    else:
        rules = default_policy_rules()

    total_fund = int(rules.get("total_fund", {}).get("amount_base_units", 17_000_000_000))
    currency = rules.get("total_fund", {}).get("currency", "XLM")

    batches = db.query(PayoutBatch).filter_by(competition_id=competition_id).order_by(PayoutBatch.created_at.asc()).all()
    batch_ids = [b.id for b in batches]

    payouts = db.query(Payout).filter(Payout.batch_id.in_(batch_ids)).all() if batch_ids else []

    paid = sum(p.amount_base_units for p in payouts if p.status in ("confirmed", "simulated"))
    reserved = sum(p.amount_base_units for p in payouts if p.status in ("authorized", "approved", "executing", "submitted"))
    unresolved = sum(p.amount_base_units for p in payouts if p.status == "unresolved")
    proposed = sum(p.amount_base_units for p in payouts if p.status == "proposed")

    # Proportional policy reserve calculation based on verified winners
    verified_count = db.query(Recipient).filter_by(competition_id=competition_id, eligibility_status="verified").count()
    policy_alloc = calculate_proportional_allocation(rules, verified_count)

    # Active batch explicit reserve check
    active_batch_reserves = [
        b.reserve_base_units
        for b in batches
        if b.status in ("confirmed", "simulated", "approved", "proposed") and b.reserve_base_units is not None
    ]
    if active_batch_reserves:
        carry_forward = active_batch_reserves[-1]
    else:
        carry_forward = policy_alloc.get("carry_forward_reserve_base_units", total_fund)

    available = max(0, total_fund - (paid + reserved + proposed + unresolved))

    return {
        "competition_id": competition_id,
        "currency": currency,
        "total_fund_base_units": total_fund,
        "total_fund_display": f"{total_fund / 10_000_000:.2f} {currency}",
        "paid_base_units": paid,
        "paid_display": f"{paid / 10_000_000:.2f} {currency}",
        "reserved_base_units": reserved,
        "reserved_display": f"{reserved / 10_000_000:.2f} {currency}",
        "unresolved_base_units": unresolved,
        "unresolved_display": f"{unresolved / 10_000_000:.2f} {currency}",
        "proposed_base_units": proposed,
        "proposed_display": f"{proposed / 10_000_000:.2f} {currency}",
        "available_base_units": available,
        "available_display": f"{available / 10_000_000:.2f} {currency}",
        "carry_forward_reserve_base_units": carry_forward,
        "carry_forward_display": f"{carry_forward / 10_000_000:.2f} {currency}",
        "accounting_invariants": {
            "no_negative_balances": available >= 0 and carry_forward >= 0,
            "commitments_within_fund": (paid + reserved + proposed + unresolved) <= total_fund
        }
    }
