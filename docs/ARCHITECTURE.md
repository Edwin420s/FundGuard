# Architecture and trust boundaries

## 1. Logical components

```text
Organizer / Approver / Auditor
            |
       React dashboard
            |
     FastAPI versioned API
            |
   AuthN / tenant / RBAC layer  [production gate]
            |
  Domain services (deterministic)
   |         |          |
Policy   Approval    Audit/evidence
   |         |
Batch & accounting / payout state machine
            |
   Settlement adapter interface
      |                    |
Simulated adapter    Stellar testnet adapter [integration required]
                           |
                    Horizon / Stellar RPC
                           |
                 independent evidence verifier

Omega / Hyperon / MeTTa adapter [integration required]
            |
  allowlisted typed tools only
            |
     Domain services (same controls)
```

## 2. Core trust boundaries

- **Browser → API:** all inputs are untrusted. Validate every field server-side.
- **Agent → tools:** the agent is a proposer/coordinator, not an authority. Tools enforce policy and authorization independently.
- **API → database:** domain services own transaction boundaries and constraints.
- **Payout service → signer:** isolated service boundary; no signer secret in browser, agent prompt, general API logs, or source control.
- **Application → blockchain:** chain submission is not confirmation. Verify the transaction and expected payment operation independently.
- **Audit log → external evidence:** application hash chaining is tamper-evident only if protected; production should periodically anchor audit roots to independently controlled storage or a public ledger.

## 3. Backend modules

- `config.py`: typed environment settings.
- `database.py`: SQLAlchemy engine/session.
- `models.py`: persistent domain entities.
- `schemas.py`: request validation.
- `services/workflows.py`: deterministic orchestration, state transitions, canonical proposal hashing, approval, simulation, and serialization.
- `services/audit.py`: append structured hash-linked audit events.
- `services/settlement.py`: adapter interface and local simulation.
- `api/routes.py`: HTTP transport layer.
- `main.py`: app assembly and local schema initialization.

## 4. Data flow

1. Organizer creates competition.
2. Recipient is registered as `pending`.
3. Authorized reviewer verifies eligibility and an audit event is appended.
4. Organizer selects verified recipients and submits a proposal with an idempotency key.
5. Domain service validates scope and eligibility, computes integer amounts, canonicalizes proposal JSON, and hashes it.
6. Approver submits the exact hash. Approval fails if it does not match.
7. Execution re-checks approval/hash and status. Local build uses simulation only.
8. Real Stellar adapter, when implemented, submits and independently verifies expected operation, destination, asset, amount, and network.
9. Payout and batch states are reconciled; audit events and receipt references are retained.
10. Exports and dashboards read persisted evidence, never generated agent claims.

## 5. Deployment topology

Local development uses React/Vite, FastAPI, and SQLite. Docker Compose uses React built into Nginx, FastAPI, and PostgreSQL. Production should add:
- TLS termination and a supported secret manager.
- authenticated identity and tenant-aware RBAC.
- dedicated signer or custody provider with policy restrictions.
- Alembic migrations rather than automatic schema creation.
- durable task queue for reconciliation and notifications.
- metrics/logging/alerts, backup and restore tests, rate limiting, and incident access controls.

## 6. Architectural decisions

See `DECISIONS.md`. The demo intentionally does not pretend to be a complete production payment processor.
