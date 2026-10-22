def test_approval_and_simulated_execution(client):
    c = client
    competition = c.post("/api/v1/competitions", json={"name": "Test Competition"}).json()
    cid = competition["id"]
    recipient = c.post(f"/api/v1/competitions/{cid}/recipients", json={
        "display_name": "Team One", "wallet_address": "GDEMOADDRESS123", "eligibility_status": "pending"
    }).json()
    verify = c.post(f"/api/v1/competitions/{cid}/recipients/{recipient['id']}/verify")
    assert verify.status_code == 200
    batch = c.post(f"/api/v1/competitions/{cid}/batches",
        headers={"Idempotency-Key": "test-batch-1"},
        json={"recipient_ids": [recipient["id"]], "amount_base_units": 1000000, "reserve_base_units": 50000}).json()
    assert batch["status"] == "proposed"
    assert batch["content_hash"].startswith("sha256:")
    wrong = c.post(f"/api/v1/batches/{batch['id']}/approve",
        json={"approver": "finance", "confirm_hash": "sha256:wrong"})
    assert wrong.status_code == 409
    approved = c.post(f"/api/v1/batches/{batch['id']}/approve",
        json={"approver": "finance-approver", "confirm_hash": batch["content_hash"]})
    assert approved.status_code == 200
    executed = c.post(f"/api/v1/batches/{batch['id']}/execute",
        json={"requested_by": "organizer", "mode": "simulated"})
    assert executed.status_code == 200
    body = executed.json()
    assert body["status"] == "simulated"
    assert body["payouts"][0]["status"] == "simulated"
    assert body["payouts"][0]["receipt"]["kind"] == "SIMULATED_NOT_ON_CHAIN"

def test_batch_requires_idempotency_key(client):
    c = client
    comp = c.post("/api/v1/competitions", json={"name": "No Key"}).json()
    r = c.post(f"/api/v1/competitions/{comp['id']}/batches",
        json={"recipient_ids": ["fake"], "amount_base_units": 100})
    assert r.status_code == 400


def test_audit_chain_integrity(client):
    c = client
    comp = c.post("/api/v1/competitions", json={"name": "Audit Test"}).json()
    cid = comp["id"]
    rec = c.post(f"/api/v1/competitions/{cid}/recipients", json={
        "display_name": "Audit Team", "wallet_address": "GAUDIT12345", "eligibility_status": "pending"
    }).json()
    c.post(f"/api/v1/competitions/{cid}/recipients/{rec['id']}/verify")
    batch = c.post(f"/api/v1/competitions/{cid}/batches",
        headers={"Idempotency-Key": "audit-batch-key-1"},
        json={"recipient_ids": [rec["id"]], "amount_base_units": 1000000, "reserve_base_units": 50000}).json()
    c.post(f"/api/v1/batches/{batch['id']}/approve",
        json={"approver": "finance", "confirm_hash": batch["content_hash"]})
    c.post(f"/api/v1/batches/{batch['id']}/execute",
        json={"requested_by": "organizer", "mode": "simulated"})

    verify_res = c.get(f"/api/v1/audit/verify?competition_id={cid}").json()
    assert verify_res["valid"] is True
    assert verify_res["event_count"] >= 4
    assert len(verify_res["invalid_event_ids"]) == 0

    export_csv = c.get(f"/api/v1/audit/export?format=csv&competition_id={cid}")
    assert export_csv.status_code == 200
    assert "integrity_valid" in export_csv.text

