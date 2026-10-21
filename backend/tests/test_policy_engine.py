from app.services.policy_engine import (
    calculate_proportional_allocation,
    canonical_json,
    compute_hash,
    default_policy_rules,
    validate_proposal,
)


def test_proportional_allocation_track_02_example():
    """
    Test the canonical Track 02 example from the buildathon brief:
    Target: 50 teams. Verified: 20 teams. Ratio: 40%.
    Fund: 17,000,000,000 stroops ($1,700 illustrative).
    Released: 6,800,000,000 stroops ($680).
    Reserve: 10,200,000,000 stroops ($1,020).
    """
    rules = default_policy_rules(target_eligible_count=50, total_fund_base_units=17_000_000_000)
    res = calculate_proportional_allocation(rules, eligible_count=20)

    assert res["target_eligible_count"] == 50
    assert res["eligible_count"] == 20
    assert res["release_ratio"] == 0.4
    assert res["released_base_units"] == 6_800_000_000
    assert res["carry_forward_reserve_base_units"] == 10_200_000_000
    assert res["allocated_total_base_units"] == 6_800_000_000
    assert res["allocated_total_base_units"] + res["total_reserve_base_units"] == 17_000_000_000
    assert res["amount_per_recipient_base_units"] == 340_000_000

def test_allocation_zero_and_full_capacity():
    rules = default_policy_rules(target_eligible_count=50, total_fund_base_units=10_000_000)

    # 0 eligible
    zero = calculate_proportional_allocation(rules, eligible_count=0)
    assert zero["release_ratio"] == 0.0
    assert zero["released_base_units"] == 0
    assert zero["total_reserve_base_units"] == 10_000_000

    # 50 eligible
    full = calculate_proportional_allocation(rules, eligible_count=50)
    assert full["release_ratio"] == 1.0
    assert full["released_base_units"] == 10_000_000
    assert full["carry_forward_reserve_base_units"] == 0

    # > 50 eligible caps at 100%
    over = calculate_proportional_allocation(rules, eligible_count=75)
    assert over["release_ratio"] == 1.0
    assert over["released_base_units"] == 10_000_000

def test_canonical_json_and_hash_stability():
    dict1 = {"b": 2, "a": 1, "c": [3, 2, 1]}
    dict2 = {"a": 1, "c": [3, 2, 1], "b": 2}
    assert canonical_json(dict1) == canonical_json(dict2)
    assert compute_hash(dict1) == compute_hash(dict2)
    assert compute_hash(dict1).startswith("sha256:")

def test_validate_proposal_detects_violations():
    rules = default_policy_rules(target_eligible_count=50, total_fund_base_units=10_000_000)

    # Case 1: Ineligible recipient
    recipients = [
        {"id": "1", "display_name": "T1", "wallet_address": "G1", "eligibility_status": "verified"},
        {"id": "2", "display_name": "T2", "wallet_address": "G2", "eligibility_status": "pending"}
    ]
    val1 = validate_proposal(recipients, 100_000, 500_000, rules)
    assert val1["valid"] is False
    assert any("Ineligible" in err for err in val1["blocking_errors"])

    # Case 2: Duplicate wallet
    recipients_dup = [
        {"id": "1", "display_name": "T1", "wallet_address": "G_SAME", "eligibility_status": "verified"},
        {"id": "2", "display_name": "T2", "wallet_address": "G_SAME", "eligibility_status": "verified"}
    ]
    val2 = validate_proposal(recipients_dup, 100_000, 500_000, rules)
    assert val2["valid"] is False
    assert any("Duplicate" in err for err in val2["blocking_errors"])

    # Case 3: Exceeding permitted release cap
    # 2 recipients out of 50 = 4% = 400,000 allowed. Requesting 2 * 300,000 = 600,000
    recipients_valid = [
        {"id": "1", "display_name": "T1", "wallet_address": "G1", "eligibility_status": "verified"},
        {"id": "2", "display_name": "T2", "wallet_address": "G2", "eligibility_status": "verified"}
    ]
    val3 = validate_proposal(recipients_valid, 300_000, 500_000, rules)
    assert val3["valid"] is False
    assert any("exceeds permitted release" in err for err in val3["blocking_errors"])
