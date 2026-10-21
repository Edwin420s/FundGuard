import hashlib
import json
from typing import Any


def canonical_json(data: Any) -> str:
    """Produces stable JSON with sorted keys and no unnecessary whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def compute_hash(data: Any) -> str:
    """Calculates a sha256: hex digest of canonical JSON."""
    raw = canonical_json(data).encode("utf-8")
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"

def default_policy_rules(target_eligible_count: int = 50, total_fund_base_units: int = 17_000_000_000,
                         currency: str = "XLM", illustrative_fiat_usd: str = "1700.00") -> dict:
    """Returns the canonical track-02 funding policy baseline."""
    return {
        "release_rule": {
            "type": "eligible_ratio",
            "target_eligible_count": target_eligible_count,
            "minimum_eligible_count": 1
        },
        "total_fund": {
            "amount_base_units": total_fund_base_units,
            "currency": currency,
            "illustrative_fiat_usd": illustrative_fiat_usd
        },
        "award_rules": [
            {
                "category": "winner",
                "share_type": "equal_split"
            }
        ],
        "reserve_rule": {
            "type": "carry_forward"
        },
        "eligibility_requirements": [
            "organizer_verified"
        ]
    }

def calculate_proportional_allocation(policy_rules: dict, eligible_count: int) -> dict:
    """
    Deterministic financial arithmetic for funding release.
    Example: 20 eligible out of 50 target with fund of 17,000,000,000 stroops:
    ratio = 20 / 50 = 0.40 (40%)
    released = 6,800,000,000 stroops ($680 illustrative)
    carry_forward_reserve = 10,200,000,000 stroops ($1020 illustrative)
    """
    total_fund = int(policy_rules.get("total_fund", {}).get("amount_base_units", 17_000_000_000))
    target_count = int(policy_rules.get("release_rule", {}).get("target_eligible_count", 50))
    min_count = int(policy_rules.get("release_rule", {}).get("minimum_eligible_count", 1))

    if eligible_count < min_count or target_count <= 0:
        ratio = 0.0
        released = 0
    else:
        ratio = min(1.0, float(eligible_count) / float(target_count))
        released = int(total_fund * ratio)

    carry_forward_reserve = total_fund - released

    if eligible_count > 0 and released > 0:
        per_recipient = released // eligible_count
        remainder = released - (per_recipient * eligible_count)
    else:
        per_recipient = 0
        remainder = 0

    total_reserve = carry_forward_reserve + remainder
    allocated_total = per_recipient * eligible_count

    # Invariant assertion
    assert allocated_total + total_reserve == total_fund, "Accounting invariant violated: allocated + reserve must equal total fund"

    return {
        "target_eligible_count": target_count,
        "eligible_count": eligible_count,
        "release_ratio": round(ratio, 4),
        "total_fund_base_units": total_fund,
        "released_base_units": released,
        "amount_per_recipient_base_units": per_recipient,
        "carry_forward_reserve_base_units": carry_forward_reserve,
        "total_reserve_base_units": total_reserve,
        "allocated_total_base_units": allocated_total,
        "illustrative_released_fiat": f"${(released / 10_000_000):.2f}" if total_fund == 17_000_000_000 else None,
        "illustrative_reserve_fiat": f"${(total_reserve / 10_000_000):.2f}" if total_fund == 17_000_000_000 else None
    }

def validate_proposal(recipients: list[dict], amount_per_recipient: int, reserve_amount: int,
                      policy_rules: dict) -> dict:
    """Validates proposal constraints deterministically."""
    checks = []
    blocking_errors = []
    warnings = []

    # 1. Eligibility check
    ineligible = [r for r in recipients if r.get("eligibility_status") != "verified"]
    if ineligible:
        names = ", ".join(r.get("display_name", r.get("id")) for r in ineligible)
        blocking_errors.append(f"Ineligible recipients found: {names}. Only verified recipients may receive payouts.")
        checks.append({"code": "ELIGIBILITY_VALID", "passed": False, "detail": f"{len(ineligible)} ineligible"})
    else:
        checks.append({"code": "ELIGIBILITY_VALID", "passed": True, "detail": f"All {len(recipients)} recipients verified"})

    # 2. Duplicate wallet addresses check
    wallets = [r.get("wallet_address") for r in recipients if r.get("wallet_address")]
    if len(wallets) != len(set(wallets)):
        blocking_errors.append("Duplicate wallet destination address found in recipient list.")
        checks.append({"code": "NO_DUPLICATE_OBLIGATIONS", "passed": False, "detail": "Duplicate wallets detected"})
    else:
        checks.append({"code": "NO_DUPLICATE_OBLIGATIONS", "passed": True, "detail": "All destinations unique"})

    # 3. Funding calculation check
    total_requested = amount_per_recipient * len(recipients)
    total_fund = int(policy_rules.get("total_fund", {}).get("amount_base_units", 17_000_000_000))
    target_count = int(policy_rules.get("release_rule", {}).get("target_eligible_count", 50))
    ratio = min(1.0, float(len(recipients)) / float(target_count))
    permitted_release = int(total_fund * ratio)

    if total_requested > permitted_release:
        blocking_errors.append(
            f"Total requested allocation ({total_requested}) exceeds permitted release ({permitted_release}) under the funding rule ({ratio*100:.1f}%)."
        )
        checks.append({"code": "FUNDING_CAP_VALID", "passed": False, "detail": f"Requested {total_requested} > Permitted {permitted_release}"})
    else:
        checks.append({"code": "FUNDING_CAP_VALID", "passed": True, "detail": f"Within permitted release {permitted_release}"})

    # 4. Total accounting check
    if total_requested + reserve_amount < total_fund:
        warnings.append(f"Allocated plus reserve ({total_requested + reserve_amount}) is less than total fund ({total_fund}).")

    checks.append({"code": "RECIPIENTS_VALID", "passed": len(recipients) > 0, "detail": f"{len(recipients)} recipients"})

    return {
        "valid": len(blocking_errors) == 0,
        "blocking_errors": blocking_errors,
        "warnings": warnings,
        "checks": checks
    }
