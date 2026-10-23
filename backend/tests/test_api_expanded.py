def test_api_organizations_and_policies(client):
    c = client
    # Organizations
    orgs = c.get("/api/v1/organizations").json()
    assert len(orgs) >= 1

    new_org = c.post("/api/v1/organizations", json={"name": "New Org", "slug": "new-org"}).json()
    assert new_org["slug"] == "new-org"

    # Competition
    comp = c.post("/api/v1/competitions", json={"name": "API Comp", "description": "Testing endpoints"}).json()
    cid = comp["id"]

    # Policies
    policies = c.get(f"/api/v1/competitions/{cid}/policies").json()
    assert len(policies) >= 1
    assert policies[0]["version"] == 1

    # Simulate policy
    sim = c.post(f"/api/v1/competitions/{cid}/policies/simulate", json={
        "target_eligible_count": 50,
        "eligible_count": 20,
        "total_fund_base_units": 17_000_000_000
    }).json()
    assert sim["calculated_outcome"]["release_ratio"] == 0.4
    assert sim["calculated_outcome"]["released_base_units"] == 6_800_000_000

    # NEAR Intents Dry Quote
    quote = c.get("/api/v1/near-intents/quote?from_asset=XLM&to_asset=NEAR&amount_base_units=10000000").json()
    assert quote["from_asset"] == "XLM"
    assert quote["to_asset"] == "NEAR"

    # Agent Run via API
    agent_run = c.post(f"/api/v1/agent/run?competition_id={cid}", json={
        "intent": "prepare_payout_proposal",
        "prompt": "Prepare payouts for verified teams"
    }).json()
    assert agent_run["status"] == "completed"

    # MeTTa Query via API
    metta_res = c.post("/api/v1/agent/metta?q=!(eligible-ratio 20 50)").json()
    assert metta_res["result"] == 0.4

    # Audit Export CSV
    csv_res = c.get(f"/api/v1/audit/export?format=csv&competition_id={cid}")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "event_hash" in csv_res.text
