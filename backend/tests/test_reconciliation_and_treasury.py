from app.database import SessionLocal
from app.services.reconciliation import (
    create_or_get_reconciliation_case,
    list_reconciliation_cases,
    resolve_reconciliation_case,
)
from app.services.treasury import get_treasury_summary


def test_treasury_and_reconciliation_lifecycle(client):
    c = client
    comp = c.post("/api/v1/competitions", json={"name": "Treasury Test"}).json()
    cid = comp["id"]

    rec = c.post(f"/api/v1/competitions/{cid}/recipients", json={"display_name": "Team A", "wallet_address": "GTEAM1"}).json()
    c.post(f"/api/v1/competitions/{cid}/recipients/{rec['id']}/verify")

    batch = c.post(f"/api/v1/competitions/{cid}/batches",
                   headers={"Idempotency-Key": "treasury-batch-1"},
                   json={"recipient_ids": [rec["id"]], "amount_base_units": 100_000_000, "reserve_base_units": 50_000_000}).json()

    db = SessionLocal()
    try:
        # Check treasury before approval
        t1 = get_treasury_summary(db, cid)
        assert t1["total_fund_base_units"] == 17_000_000_000
        assert t1["proposed_base_units"] == 100_000_000
        assert t1["paid_base_units"] == 0

        # Approve
        c.post(f"/api/v1/batches/{batch['id']}/approve", json={"approver": "finance", "confirm_hash": batch["content_hash"]})

        # Check treasury after approval
        t2 = get_treasury_summary(db, cid)
        assert t2["reserved_base_units"] == 100_000_000

        # Execute simulated
        c.post(f"/api/v1/batches/{batch['id']}/execute", json={"requested_by": "organizer", "mode": "simulated"})

        # Check treasury after simulated payout
        t3 = get_treasury_summary(db, cid)
        assert t3["paid_base_units"] == 100_000_000
        assert t3["reserved_base_units"] == 0

        # Create reconciliation case
        payout_id = batch["payouts"][0]["id"]
        case = create_or_get_reconciliation_case(db, payout_id, "Testnet timeout occurred")
        assert case.status == "open"
        assert case.payout_id == payout_id

        cases = list_reconciliation_cases(db, cid)
        assert len(cases) >= 1

        # Resolve case
        res = resolve_reconciliation_case(db, case.id, decision="confirm", reviewer="auditor",
                                          resolution_note="Manually verified on testnet explorer")
        assert res["status"] == "resolved_confirmed"
    finally:
        db.close()
