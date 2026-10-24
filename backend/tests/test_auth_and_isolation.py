def test_auth_registration_and_login(client):
    c = client

    # 1. Register a new user and organization
    reg_payload = {
        "full_name": "Alice Auditor",
        "email": "alice@foundation.org",
        "password": "StrongPassword123!",
        "organization_name": "Alpha Foundation",
        "role": "organizer"
    }
    reg_res = c.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["user"]["email"] == "alice@foundation.org"
    assert reg_data["user"]["full_name"] == "Alice Auditor"
    assert reg_data["user"]["organization_name"] == "Alpha Foundation"
    assert reg_data["token"] is not None
    assert reg_data["default_competition_id"] is not None

    assert reg_data["user"]["organization_id"] is not None
    comp_id_alpha = reg_data["default_competition_id"]

    # 2. Reject duplicate email registration
    dup_res = c.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 409

    # 3. Reject invalid email format
    bad_email_res = c.post("/api/v1/auth/register", json={
        "full_name": "Invalid User",
        "email": "not-an-email",
        "password": "Password123!",
        "organization_name": "Bad Org"
    })
    assert bad_email_res.status_code == 400

    # 4. Authenticate user
    login_res = c.post("/api/v1/auth/login", json={
        "email": "alice@foundation.org",
        "password": "StrongPassword123!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["id"] == reg_data["user"]["id"]
    assert login_data["default_competition_id"] == comp_id_alpha

    # 5. Reject invalid password
    bad_pwd_res = c.post("/api/v1/auth/login", json={
        "email": "alice@foundation.org",
        "password": "WrongPassword!"
    })
    assert bad_pwd_res.status_code == 401


def test_multi_tenant_workspace_and_audit_isolation(client):
    c = client

    # User A in Organization Alpha
    user_a = c.post("/api/v1/auth/register", json={
        "full_name": "User Alpha",
        "email": "alpha@example.org",
        "password": "PasswordAlpha123!",
        "organization_name": "Alpha Corp"
    }).json()
    org_a = user_a["user"]["organization_id"]
    comp_a = user_a["default_competition_id"]

    # User B in Organization Beta
    user_b = c.post("/api/v1/auth/register", json={
        "full_name": "User Beta",
        "email": "beta@example.org",
        "password": "PasswordBeta123!",
        "organization_name": "Beta Corp"
    }).json()
    org_b = user_b["user"]["organization_id"]
    comp_b = user_b["default_competition_id"]

    assert org_a != org_b
    assert comp_a != comp_b

    # Add recipient and batch in Alpha's competition
    valid_key = "GA7SFOTHBSSRUGL4NUYZXCQTO2MDDJYUIEVPYIYPCYD2BR2RQOVNXIHD"
    rec_a = c.post(f"/api/v1/competitions/{comp_a}/recipients", json={
        "display_name": "Alpha Winner",
        "wallet_address": valid_key
    }).json()
    c.post(f"/api/v1/competitions/{comp_a}/recipients/{rec_a['id']}/verify")

    batch_a = c.post(f"/api/v1/competitions/{comp_a}/batches",
                     headers={"Idempotency-Key": "alpha-batch-001"},
                     json={
                         "recipient_ids": [rec_a["id"]],
                         "amount_base_units": 100_000_000,
                         "reserve_base_units": 900_000_000
                     }).json()
    c.post(f"/api/v1/batches/{batch_a['id']}/approve", json={
        "approver": "Alpha Approver",
        "confirm_hash": batch_a["content_hash"]
    })
    c.post(f"/api/v1/batches/{batch_a['id']}/execute", json={
        "requested_by": "Alpha Lead",
        "mode": "simulated"
    })

    # Verify Beta's workspace is completely isolated:
    # 1. Competitions filtered by org_b returns only comp_b
    beta_comps = c.get(f"/api/v1/competitions?organization_id={org_b}").json()
    assert len(beta_comps) == 1
    assert beta_comps[0]["id"] == comp_b
    assert beta_comps[0]["organization_id"] == org_b

    # 2. Beta's recipients list has 0 recipients
    beta_recipients = c.get(f"/api/v1/competitions/{comp_b}/recipients").json()
    assert len(beta_recipients) == 0

    # 3. Beta's batches list has 0 batches
    beta_batches = c.get(f"/api/v1/competitions/{comp_b}/batches").json()
    assert len(beta_batches) == 0

    # 4. Beta's treasury summary has 0 settled disbursements
    beta_treasury = c.get(f"/api/v1/treasury/{comp_b}").json()
    assert beta_treasury["paid_base_units"] == 0
    assert beta_treasury["reserved_base_units"] == 0
    assert beta_treasury["proposed_base_units"] == 0
    assert beta_treasury["available_base_units"] == beta_treasury["total_fund_base_units"]

    # 5. Beta's audit events only contain Beta workspace creation events
    beta_audit = c.get(f"/api/v1/audit/events?competition_id={comp_b}").json()
    for evt in beta_audit:
        assert evt["competition_id"] == comp_b
        assert "Alpha" not in str(evt)
