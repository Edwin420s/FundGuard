#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE_URL:-http://127.0.0.1:8000/api/v1}"

echo "============================================================"
echo "  Omega FundGuard - End-to-End Payout Coordination Demo"
echo "============================================================"

# 1. Health check
echo -e "\n[1/13] Checking API Health..."
curl -fsS "$BASE/health"
echo ""

# 2. Create competition
echo -e "\n[2/13] Creating Hackathon Competition Workspace..."
COMP="$(curl -fsS -X POST "$BASE/competitions" \
  -H 'Content-Type: application/json' \
  -d '{"name":"BASIX Lisbon AI Omega Buildathon","description":"Track 02 Prize Fund Distribution","network":"stellar-testnet"}')"
CID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<< "$COMP")"
echo "Competition created: $CID"

# 3. Inspect policy version
echo -e "\n[3/13] Retrieving Versioned Funding Policy..."
curl -fsS "$BASE/competitions/$CID/policies" | python3 -m json.tool | head -n 30

# 4. Stellar Testnet Keypair Generation & Custody Query
echo -e "\n[4/13] Stellar Testnet Custody & Ed25519 StrKey Generation..."
curl -fsS "$BASE/stellar/custody" | python3 -m json.tool | head -n 15
GEN_KP1="$(curl -fsS -X POST "$BASE/stellar/generate-keypair?fund_via_friendbot=false")"
TESTNET_PK1="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["public_key"])' <<< "$GEN_KP1")"
GEN_KP2="$(curl -fsS -X POST "$BASE/stellar/generate-keypair?fund_via_friendbot=false")"
TESTNET_PK2="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["public_key"])' <<< "$GEN_KP2")"
echo "Generated valid testnet recipient keypairs: $TESTNET_PK1 and $TESTNET_PK2"

# 5. Register recipients
echo -e "\n[5/13] Registering Winning Teams..."
R1="$(curl -fsS -X POST "$BASE/competitions/$CID/recipients" \
  -H 'Content-Type: application/json' \
  -d "{\"display_name\":\"Team Northstar\",\"wallet_address\":\"$TESTNET_PK1\"}")"
RID1="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<< "$R1")"

R2="$(curl -fsS -X POST "$BASE/competitions/$CID/recipients" \
  -H 'Content-Type: application/json' \
  -d "{\"display_name\":\"Team MeTTaLogic\",\"wallet_address\":\"$TESTNET_PK2\"}")"
RID2="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<< "$R2")"

echo "Registered: $RID1 (Team Northstar) and $RID2 (Team MeTTaLogic)"

# 6. Verify recipients
echo -e "\n[6/13] Reviewer Verifying Recipient Eligibility..."
curl -fsS -X POST "$BASE/competitions/$CID/recipients/$RID1/verify"
curl -fsS -X POST "$BASE/competitions/$CID/recipients/$RID2/verify"
echo "Recipients verified."

# 7. Run Omega MeTTa Agent
echo -e "\n[7/13] Running Omega Agent MeTTa Reasoning & Tool Coordination..."
AGENT_RUN="$(curl -fsS -X POST "$BASE/agent/run?competition_id=$CID" \
  -H 'Content-Type: application/json' \
  -d '{"intent":"prepare_payout_proposal","prompt":"Prepare payouts for verified winning teams and calculate reserve."}')"
echo "$AGENT_RUN" | python3 -m json.tool

# 8. Create proposal batch with idempotency key
echo -e "\n[8/13] Proposing Payout Batch with Idempotency Key..."
BATCH="$(curl -fsS -X POST "$BASE/competitions/$CID/batches" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-batch-idempotency-key-001' \
  -d "{\"recipient_ids\":[\"$RID1\",\"$RID2\"],\"amount_base_units\":3400000000,\"reserve_base_units\":10200000000,\"asset_code\":\"XLM\",\"asset_type\":\"native\"}")"
BID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<< "$BATCH")"
HASH="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["content_hash"])' <<< "$BATCH")"
echo "Batch created: $BID"
echo "Canonical content hash: $HASH"

# 9. Human approval bound to exact hash
echo -e "\n[9/13] Human Approving Exact Batch Content Hash..."
curl -fsS -X POST "$BASE/batches/$BID/approve" \
  -H 'Content-Type: application/json' \
  -d "{\"approver\":\"Finance Approver\",\"role\":\"finance_approver\",\"decision\":\"approved\",\"confirm_hash\":\"$HASH\",\"reason\":\"Reviewed 2 eligible teams under 40% release rule\"}" \
  | python3 -m json.tool | head -n 25

# 10. Execute payouts
echo -e "\n[10/13] Executing Payout Settlement..."
curl -fsS -X POST "$BASE/batches/$BID/execute" \
  -H 'Content-Type: application/json' \
  -d '{"requested_by":"Competition Organizer","mode":"simulated"}' \
  | python3 -m json.tool | head -n 35

# 11. Closed-Loop Learning & Dynamic MeTTa Rules
echo -e "\n[11/13] Closed-Loop Learning & Dynamic MeTTa Rule Registration..."
curl -fsS -X POST "$BASE/agent/learning/feedback?competition_id=$CID" \
  -H 'Content-Type: application/json' \
  -d "{\"recipient_id\":\"$RID1\",\"outcome\":\"confirmed_settlement\",\"reviewer\":\"Senior Auditor\",\"feedback_note\":\"Verified on-chain receipt proof\"}" \
  | python3 -m json.tool

curl -fsS -X POST "$BASE/agent/learning/rules" \
  -H 'Content-Type: application/json' \
  -d "{\"competition_id\":\"$CID\",\"rule_name\":\"max-payout-award-cap\",\"rule_expression\":\"3400000000\",\"created_by\":\"Finance Supervisor\",\"rationale\":\"Cap individual team award at 340 XLM\"}" \
  | python3 -m json.tool

echo "--- Active Learning Matrix ---"
curl -fsS "$BASE/agent/learning/insights?competition_id=$CID" | python3 -m json.tool | head -n 30

# 12. NEAR Intents Cross-Chain Leg Dry Quote
echo -e "\n[12/13] Requesting NEAR Intents Dry Quote (Simulation)..."
curl -fsS "$BASE/near-intents/quote?from_asset=XLM&to_asset=NEAR&amount_base_units=10000000" | python3 -m json.tool

# 13. Treasury & Audit Verification
echo -e "\n[13/13] Verifying Treasury Ledger & Audit Event Chain..."
echo "--- Treasury Summary ---"
curl -fsS "$BASE/treasury/$CID" | python3 -m json.tool
echo "--- Audit Chain Integrity ---"
curl -fsS "$BASE/audit/verify?competition_id=$CID" | python3 -m json.tool

echo -e "\n============================================================"
echo "  Omega FundGuard Demo Completed Successfully!"
echo "============================================================"
