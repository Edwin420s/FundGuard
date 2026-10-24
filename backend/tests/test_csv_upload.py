import io

def test_csv_template_endpoint(client):
    c = client
    comp = c.post("/api/v1/competitions", json={"name": "CSV Test Comp"}).json()
    cid = comp["id"]

    res = c.get(f"/api/v1/competitions/{cid}/recipients/template.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "name,wallet_address,notes" in res.text
    assert "Alpha Pioneers" in res.text


def test_bulk_recipients_api(client):
    c = client
    comp = c.post("/api/v1/competitions", json={"name": "Bulk Test Comp"}).json()
    cid = comp["id"]

    valid_wallet_1 = "GA7SFOTHBSSRUGL4NUYZXCQTO2MDDJYUIEVPYIYPCYD2BR2RQOVNXIHD"
    valid_wallet_2 = "GB2GGSI4Q4JUC2K4HSCDYDK5XAZQD5DXTRC3COL4QZRHLZBSGDK4DPVW"

    payload = {
        "recipients": [
            {"display_name": "Team One", "wallet_address": valid_wallet_1, "eligibility_note": "Finalist 1"},
            {"display_name": "Team Two", "wallet_address": valid_wallet_2, "eligibility_note": "Finalist 2"},
            {"display_name": "Bad Wallet Team", "wallet_address": "INVALID_WALLET_KEY", "eligibility_note": "Should fail"},
            {"display_name": "", "wallet_address": "GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "eligibility_note": "Empty name"}
        ],
        "auto_verify": True,
        "reviewer": "Test Reviewer"
    }

    res = c.post(f"/api/v1/competitions/{cid}/recipients/bulk", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 4
    assert data["imported_count"] == 2
    assert data["skipped_count"] == 2
    assert len(data["recipients"]) == 2
    assert data["recipients"][0]["eligibility_status"] == "verified"
    assert len(data["errors"]) == 2

    # Verify duplicate prevention
    res_dup = c.post(f"/api/v1/competitions/{cid}/recipients/bulk", json={
        "recipients": [
            {"display_name": "Team One Duplicate", "wallet_address": valid_wallet_1}
        ]
    })
    assert res_dup.status_code == 200
    dup_data = res_dup.json()
    assert dup_data["imported_count"] == 0
    assert dup_data["skipped_count"] == 1
    assert "already registered" in dup_data["errors"][0]["error"]


def test_csv_file_upload_api(client):
    c = client
    comp = c.post("/api/v1/competitions", json={"name": "Upload CSV Comp"}).json()
    cid = comp["id"]

    valid_wallet_1 = "GA7SFOTHBSSRUGL4NUYZXCQTO2MDDJYUIEVPYIYPCYD2BR2RQOVNXIHD"
    valid_wallet_2 = "GB2GGSI4Q4JUC2K4HSCDYDK5XAZQD5DXTRC3COL4QZRHLZBSGDK4DPVW"

    csv_content = (
        "team_name,public_key,review_notes\n"
        f"Robotics Lab,{valid_wallet_1},Winner category A\n"
        f"Quantum Protocol,{valid_wallet_2},Winner category B\n"
        "Bad Key Corp,G12345Short,Invalid key\n"
    )

    files = {"file": ("test_recipients.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"auto_verify": "true", "reviewer": "Audit Executive"}

    res = c.post(f"/api/v1/competitions/{cid}/recipients/upload-csv", files=files, data=data)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["total"] == 3
    assert res_json["imported_count"] == 2
    assert res_json["skipped_count"] == 1
    assert res_json["recipients"][0]["display_name"] == "Robotics Lab"
    assert res_json["recipients"][0]["eligibility_status"] == "verified"

    # Verify audit event recorded
    audit_res = c.get(f"/api/v1/audit/events?competition_id={cid}")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()]
    assert "recipients.bulk_imported" in actions
