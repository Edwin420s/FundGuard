# API Reference

Base path: `/api/v1`. OpenAPI Interactive UI: `/docs`. JSON responses.

---

## Health & System

- `GET /health`
  Returns service status: `{"status": "ok", "service": "omega-fundguard-api"}`.

---

## Organizations & Multi-Tenancy

- `GET /organizations` — List all registered organizations.
- `POST /organizations` — Register a tenant organization.
  ```json
  {"name": "Global Innovation Foundation", "slug": "global-innovation"}
  ```

---

## Competitions & Workspaces

- `GET /competitions` — List competitions.
- `POST /competitions` — Create competition workspace.
  ```json
  {
    "name": "Global Tech Grant Fund",
    "description": "Enterprise prize distribution and grant management",
    "network": "stellar-testnet"
  }
  ```
- `GET /competitions/{competition_id}` — Get competition details.

---

## Funding Policies & Proportional Engine

- `GET /competitions/{competition_id}/policies` — List versioned policies for the competition.
- `POST /competitions/{competition_id}/policies` — Create new policy version with canonical SHA-256 rule hash.
- `POST /policies/simulate` — Deterministic policy simulation endpoint for proportional release calculations.
  ```json
  {
    "total_fund_base_units": 17000000000,
    "target_eligible_count": 50,
    "eligible_count": 20,
    "currency": "XLM"
  }
  ```
  Returns:
  ```json
  {
    "target_eligible_count": 50,
    "eligible_count": 20,
    "release_ratio": 0.4,
    "total_fund_base_units": 17000000000,
    "released_base_units": 6800000000,
    "amount_per_recipient_base_units": 340000000,
    "carry_forward_reserve_base_units": 10200000000,
    "illustrative_released_fiat": "$680.00",
    "illustrative_reserve_fiat": "$1020.00"
  }
  ```

---

## Recipients & Eligibility

- `GET /competitions/{competition_id}/recipients` — List recipients for competition.
- `POST /competitions/{competition_id}/recipients` — Register recipient (validated via Stellar SDK `StrKey`).
  ```json
  {
    "display_name": "Team Northstar",
    "wallet_address": "GBZXN7PIRZGNMHGA728R420SFUNDGUARDDEMO1234567890ABCDEF12345678",
    "eligibility_status": "pending",
    "eligibility_note": "Verified Grant Winner"
  }
  ```
- `POST /competitions/{competition_id}/recipients/{recipient_id}/verify` — Organizer review and eligibility verification.

---

## Payout Batches & Human Approval Binding

- `GET /competitions/{competition_id}/batches` — List batches.
- `POST /competitions/{competition_id}/batches` — Propose batch (requires `Idempotency-Key` header).
  ```json
  {
    "recipient_ids": ["<recipient-uuid-1>", "<recipient-uuid-2>"],
    "amount_base_units": 3400000000,
    "reserve_base_units": 10200000000,
    "asset_code": "XLM",
    "asset_type": "native"
  }
  ```
- `GET /batches/{batch_id}` — Get batch details, payouts, and approvals.
- `POST /batches/{batch_id}/validate` — Deterministic validation against active policy rules.
- `POST /batches/{batch_id}/approve` — Human approval bound to exact canonical SHA-256 batch hash.
  ```json
  {
    "approver": "Finance Approver",
    "role": "finance_approver",
    "decision": "approved",
    "confirm_hash": "sha256:<exact-content-hash>",
    "reason": "Reviewed eligible teams under 40% proportional release policy"
  }
  ```
- `POST /batches/{batch_id}/execute` — Execute payouts via `simulated` or `stellar_testnet` settlement adapter.
  ```json
  {
    "requested_by": "Competition Organizer",
    "mode": "simulated"
  }
  ```

---

## Payouts & Reconciliation

- `GET /payouts/{payout_id}` — Get individual payout status, transaction hash, and receipt.
- `POST /payouts/{payout_id}/reconcile` — Re-query Horizon testnet or inspect status of unresolved payout.
- `GET /treasury/{competition_id}` — Real-time balance breakdown:
  ```json
  {
    "competition_id": "...",
    "currency": "XLM",
    "total_fund_base_units": 17000000000,
    "paid_base_units": 6800000000,
    "reserved_base_units": 0,
    "unresolved_base_units": 0,
    "available_base_units": 10200000000,
    "carry_forward_reserve_base_units": 10200000000,
    "accounting_invariants": {
      "no_negative_balances": true,
      "commitments_within_fund": true
    }
  }
  ```
- `GET /reconciliation/cases` — List active reconciliation cases.
- `POST /reconciliation/cases/{case_id}/resolve` — Manual resolution of ambiguous network submissions.

---

## Omega AI Agent & MeTTa Symbolic Engine

- `POST /agent/run?competition_id={competition_id}` — Run AI agent orchestration workflow.
  ```json
  {
    "intent": "prepare_payout_proposal",
    "prompt": "Prepare payouts for verified winning teams and calculate reserve."
  }
  ```
  Returns multi-step execution summary, MeTTa reduction traces, and allowlisted tool call details.
- `GET /agent/eval?competition_id={competition_id}` — Run 5-benchmark adversarial evaluation suite.
- `POST /agent/metta?q={query}` — Query the MeTTa symbolic knowledge base directly.
  Example query: `(calculate-release 17000000000 0.40)`
  Returns:
  ```json
  {
    "query": "(calculate-release 17000000000 0.40)",
    "result": "6800000000.0",
    "traces": [
      {"query": "(calculate-release 17000000000 0.40)", "reduction": "6800000000.0"}
    ]
  }
  ```

---

## NEAR Intents Cross-Chain Simulation

- `GET /near-intents/quote?from_asset=XLM&to_asset=NEAR&amount_base_units=10000000`
- `POST /near-intents/quote`
  Returns simulated cross-chain swap rate, output amounts, fee breakdown, and estimated slippage.

---

## Cryptographic Audit Trail

- `GET /audit/events?competition_id={competition_id}` — List hash-chained audit events.
- `GET /audit/verify?competition_id={competition_id}` — Cryptographic verification of SHA-256 event hash chain.
- `GET /audit/export?format=csv&competition_id={competition_id}` — Export tamper-evident audit history as CSV.
- `GET /audit/export?format=json&competition_id={competition_id}` — Export tamper-evident audit history as JSON.
