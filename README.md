# Omega FundGuard

**AI-agent-coordinated, human-approved, auditable payout operations for hackathons, grants, accelerators, and competitions.**

Omega FundGuard helps an organizer define funding rules, register recipients, calculate allocations, review a payout batch, obtain explicit human approval, submit authorized testnet payouts, verify network evidence, and reconcile the outcome. The application—not the LLM—is the financial system of record.

> **Safety status:** The included local demo uses a deterministic simulated settlement adapter by default. It does not send money. Stellar testnet execution is an explicitly configured integration and must not be described as active until its adapter, credentials, network configuration, and end-to-end tests have been completed. Mainnet/live-money execution is disabled by design.

## What is in this folder?

- `backend/` — FastAPI API, domain services, SQLAlchemy persistence, audit events, policy calculations, approval flow, payout state, and settlement adapter boundary.
- `frontend/` — React + Vite organizer dashboard.
- `docs/` — product, architecture, data model, API, security, operations, test plan, demo script, and milestone acceptance criteria.
- `scripts/` — local setup and demo helpers.
- `docker-compose.yml` — local app + PostgreSQL deployment.
- `.env.example` — non-secret configuration template.

## Current implementation status

| Capability | Included status | Verification / Evidence |
|---|---|---|
| Local API and dashboard | Implemented | 11-tab React dashboard, Vite production build verified |
| Full 15-entity domain model & Alembic | Implemented | `f2c511826601_initial_full_schema.py` migration applied |
| Competition & recipient records | Implemented | StrKey validation (`GBZX...`), organizer verification workflow |
| Deterministic policy engine | Implemented | Track 02 proportional release formula (e.g. 20/50 target = 40% release) |
| MeTTa symbolic reasoning engine | Implemented | `metta_engine.py`, `rules.metta`, query reduction traces |
| Omega AI Agent & 11 domain tools | Implemented | `orchestrator.py`, `AgentRun`, `AgentToolCall`, 5-benchmark adversarial suite |
| Human approval bound to batch content hash | Implemented | Exact SHA-256 canonical hash verification |
| Settlement adapter (Simulated & Stellar Testnet) | Implemented | StrKey validation, transaction builder, independent Horizon verification |
| NEAR Intents cross-chain quote simulator | Implemented | `/api/v1/near-intents/quote` dry quote calculator |
| Treasury & carry-forward reserve accounting | Implemented | Integer base-unit ledger, invariant checking, carry-forward tracking |
| Reconciliation & partial settlements | Implemented | `ReconciliationCase`, per-payout states, manual review tools |
| Audit event trail & export | Implemented | Per-competition SHA-256 hash chain, JSON & CSV export |
| Automated test suite | Implemented | 16 pytest backend tests passing 100%, Vitest passing |
| Mainnet payouts | Intentionally disabled | Safety invariant enforced in adapter boundary |


## Quick start (local Python API + frontend)

Requirements: Python 3.11+, Node.js 20+, npm.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload
```

API docs: <http://127.0.0.1:8000/docs>

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173>.

The frontend expects the API at `http://127.0.0.1:8000`. This local mode uses SQLite unless `DATABASE_URL` is set.

### 3. Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:5173> and <http://localhost:8000/docs>. Compose uses PostgreSQL. For a disposable local database, `docker compose down -v` removes the database volume.

## First demo flow

1. Start the API and UI.
2. Create a competition from the dashboard.
3. Register at least one recipient with a valid-looking Stellar test address for demo purposes.
4. Create a payout batch with an explicit asset amount per recipient.
5. Inspect the generated batch hash and totals.
6. Approve the exact batch hash.
7. Execute only in `simulated` mode unless a real, reviewed Stellar testnet adapter has been configured.
8. Inspect payout statuses and the audit trail.

The local simulation is not proof of a Stellar transaction. Its receipts are labelled `SIMULATED`.

## Environment

See `.env.example`. Never commit `.env`, private keys, Stellar secret seeds, tokens, or real recipient data.

## Development commands

```bash
cd backend
pytest
ruff check app tests
```

```bash
cd frontend
npm test
npm run build
```

## Product invariants

1. No payout executes without an explicit human approval bound to the current batch hash.
2. Changing the batch after approval invalidates that approval.
3. A submitted transaction is not marked confirmed until network evidence is independently verified.
4. An uncertain outcome is `unresolved`; it is never blindly retried.
5. An idempotency key prevents duplicate batch creation for the same request scope.
6. The agent cannot sign transactions, read signing secrets, bypass approvals, or modify audit history.
7. Fiat valuation and blockchain asset units are separate. The app never silently converts USD to XLM.
8. Mainnet is rejected by default.

## Documentation map

Start with `docs/INDEX.md`, then `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/DOMAIN_MODEL.md`, and `docs/IMPLEMENTATION_MILESTONES.md`.
