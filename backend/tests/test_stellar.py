from stellar_sdk import Keypair

from app.services.settlement import get_settlement_adapter
from app.services.stellar_service import (
    simulate_near_intents_quote,
    stroops_to_xlm_string,
    validate_stellar_address,
)


def test_stellar_strkey_validation():
    # Valid ed25519 keypair
    kp = Keypair.random()
    assert validate_stellar_address(kp.public_key) is True

    # Invalid addresses
    assert validate_stellar_address("") is False
    assert validate_stellar_address("not-an-address") is False
    assert validate_stellar_address("0x1234567890abcdef") is False
    assert validate_stellar_address("GBADLENGTH123") is False

def test_stroops_conversion():
    assert stroops_to_xlm_string(10_000_000) == "1.0000000"
    assert stroops_to_xlm_string(6_800_000_000) == "680.0000000"
    assert stroops_to_xlm_string(340_000_000) == "34.0000000"
    assert stroops_to_xlm_string(100) == "0.0000100"

def test_settlement_adapter_modes():
    sim_adapter = get_settlement_adapter("simulated")
    assert sim_adapter.network == "simulated"
    res_sim = sim_adapter.submit_and_verify(destination="GDEMO123", amount_base_units=1000)
    assert res_sim.status == "simulated"
    assert res_sim.receipt["kind"] == "SIMULATED_NOT_ON_CHAIN"

    testnet_adapter = get_settlement_adapter("stellar-testnet")
    assert testnet_adapter.network == "stellar-testnet"
    kp = Keypair.random()
    res_testnet = testnet_adapter.submit_and_verify(destination=kp.public_key, amount_base_units=5000)
    assert res_testnet.status in ("simulated", "confirmed")
    assert res_testnet.tx_hash is not None

def test_near_intents_dry_quote():
    quote = simulate_near_intents_quote(from_asset="XLM", to_asset="NEAR", amount_base_units=100_000_000)
    assert quote["from_asset"] == "XLM"
    assert quote["to_asset"] == "NEAR"
    assert "source_amount_display" in quote
    assert "estimated_destination_amount" in quote
    assert quote["quote_id"].startswith("near-quote-")
    assert "Simulated dry quote" in quote["disclaimer"]


def test_stellar_custody_and_keypair_generation(client):
    c = client
    # 1. Get custody status
    custody = c.get("/api/v1/stellar/custody").json()
    assert "account_id" in custody
    assert custody["network"] == "stellar-testnet"

    # 2. Generate valid testnet keypair
    kp_res = c.post("/api/v1/stellar/generate-keypair?fund_via_friendbot=false").json()
    assert kp_res["is_valid_strkey"] is True
    assert kp_res["public_key"].startswith("G")
    assert len(kp_res["public_key"]) == 56


def test_stellar_verify_tx_endpoint(client):
    c = client
    # Query with simulated hash
    res = c.post("/api/v1/stellar/verify-tx?tx_hash=nonexistenthash123&destination=GAAA&amount_base_units=1000").json()
    assert res["verified"] is False
    assert "not found" in res["reason"].lower() or "error" in res["reason"].lower()

