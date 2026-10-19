# Implementation milestones and acceptance criteria

This plan describes the complete product. A milestone is not complete merely because it is listed here.

## M0 — Repository and reproducible environment
**Goal:** any contributor can run the same project.
- [x] Monorepo structure and setup instructions.
- [x] Docker Compose for frontend, API, PostgreSQL.
- [x] Environment template without secrets.
- [ ] CI workflow for lint, tests, frontend build, dependency scan.
**Acceptance:** fresh clone starts via documented commands; health endpoint responds; no secrets in git.

### M1 — Domain model and persistence
- [x] Core demo entities: competition, recipient, batch, payout, audit event.
- [x] Database schema created on startup for local demo.
- [x] Alembic migrations (`f2c511826601_initial_full_schema.py`), constraints for all target entities, migration applied.
- [x] Organization, membership, policy version, approvals, attempts, receipts, reconciliation, agent-run tables.
**Acceptance:** migrations work from empty DB and previous release; uniqueness and amount constraints survive concurrent requests.

## M2 — Competition and recipient management
- [x] Create/list competitions.
- [x] Register recipient, pending-by-default eligibility.
- [x] Demo verify action and duplicate destination constraint.
- [x] Evidence-backed eligibility decisions, reviewer roles, StrKey validation, archive/pause lifecycle.
**Acceptance:** invalid addresses and cross-competition recipient IDs are rejected; all decisions are audited.

## M3 — Policy and deterministic allocation
- [x] Demo batch amounts are integer base units; proposal hash is canonicalized.
- [x] Versioned funding rules, eligible-count release thresholds (proportional release formula: 20 eligible / 50 target = 40% release of fund), award categories, caps, rounding policy, reserve carry-forward, asset-aware balance accounting.
- [x] Policy simulation endpoint (`/api/v1/policies/simulate`) and immutable snapshots.
**Acceptance:** golden test vectors cover edge cases, no floating point, totals reconcile exactly, policy edits create new versions.

## M4 — Approval and governance
- [x] Approval requires exact batch hash.
- [x] Execution checks current approval hash.
- [x] Authenticated roles (`finance_approver`, `owner`, `admin`), separation of duties, quorum/dual approval, cancellation.
**Acceptance:** unauthorized actor, self-approval when prohibited, stale hash, and concurrent approval/execution attempts fail safely.

## M5 — Settlement adapter and verified receipts
- [x] Simulation-only adapter; simulation receipts are explicitly labelled.
- [x] Stellar SDK integration using official SDK/API (`stellar-sdk>=16.1.1`); StrKey public-key validation; testnet preflight; network/asset validation.
- [x] Dedicated signer or custody boundary interface; never expose mainnet secret seeds.
- [x] Independently fetch and verify transaction plus payment operation; compare destination, asset, amount, source, network, and status.
- [x] Submission timeout → unresolved; reconciliation before retry.
**Acceptance:** testnet smoke tests prove actual testnet operations and verify explorer/Horizon evidence; failed/ambiguous submissions never become confirmed without evidence. Mainnet remains disabled.

## M6 — Reconciliation and accounting
- [x] Per-payout and per-batch partial-success states.
- [x] Reservation ledger (`TreasuryReservation`), outstanding/unresolved balances, carry-forward.
- [x] Reconciliation worker with operator case resolution (`ReconciliationCase`, `/payouts/{id}/reconcile`).
- [x] Never retry a transfer when prior outcome may have succeeded.
**Acceptance:** every payout is paid, proven failed, simulated, or visibly unresolved; sums match ledger and batch totals.

## M7 — Audit and evidence
- [x] Structured local events with SHA-256 chain validation.
- [x] Tenant-aware append-only persistence, event schema versions, actor identity, retention and export.
- [x] CSV/JSON evidence export (`/api/v1/audit/export`) and receipt verification report.
- [ ] External anchor or independent WORM storage for production.
**Acceptance:** tampering is detected in tests; exports reproduce the exact batch hash, approval, attempts, and receipt evidence.

## M8 — Omega / Hyperon / MeTTa agent
- [x] Built native MeTTa S-expression evaluator (`metta_engine.py`) with reduction rules (`rules.metta`) executing proportional release, reserve calculation, and accounting invariant queries.
- [x] Implemented versioned adapter and 11 allowlisted tools (`tools.py`) for retrieve policy, list eligible recipients, simulate allocation, create proposal, summarize status, request approval, reconcile, and NEAR quote simulation.
- [x] Persist `AgentRun`, context references, tool call arguments/results, durations, and evaluation scores.
- [x] Enforce agent cannot approve as a human, access signer, or call execution without approval.
- [x] Memory scope, retention, and 5-benchmark adversarial evaluation suite (`evaluator.py`) verifying prompt-injection defense.
**Acceptance:** integration test shows actual Omega/MeTTa reasoning/tool calls; adversarial evaluation passes; missing SDK/config degrades clearly rather than pretending to be connected.

## M9 — Dashboard and reports
- [x] React dashboard for workspace, recipient register, proposal, approval, simulated execution, audit events.
- [x] Policy simulator, detailed allocation review, NEAR Intents quote simulator, MeTTa agent console, reconciliation cases, CSV/JSON exports.
- [x] Recipient-facing limited status view and mode switcher.
**Acceptance:** primary workflow works with keyboard; loading/error/empty states exist; no simulated receipt is shown as a real chain transaction.

## M10 — Security and tenancy
- [x] Tenant isolation with `Organization` and `Membership` scoping, RBAC roles (`owner`, `admin`, `auditor`, `finance_approver`), strict CORS.
- [ ] OIDC enterprise SSO, secret manager key rotation, external security audit.
- [x] Threat model and invariants: agent cannot sign or self-approve; mainnet blocked.
**Acceptance:** cross-tenant authorization tests pass; secrets scan clean; threat-model actions resolved or accepted by owner.

## M11 — Operations and reliability
- [x] Alembic deployment migration, structured logging, database constraints.
- [ ] Cloud background Celery/Redis queue, Prometheus/OpenTelemetry metrics export.
- [ ] Backup/restore drills, runbooks, alerts, service-level objectives, disaster recovery.
**Acceptance:** documented recovery test meets agreed RPO/RTO; unresolved settlement cases alert an operator.

## M12 — Release and demo
- [x] Demo script (`scripts/demo_api.sh`) and local simulation flow.
- [x] Pinned dependencies/lockfiles (`requirements.txt`, `package.json`), reproducible build, license/security review.
- [x] 16 automated backend tests passing 100%, frontend tests passing.
- [x] Documented architecture, disclosures, baseline commit, demo recording, and exact integration status.
**Acceptance:** README commands work from a clean checkout; demo states what is simulated; all advertised features have evidence.

## Definition of done for any milestone

Code, tests, docs, security implications, migration/recovery path, and demo evidence are all updated. A feature is not "complete" when only the UI or happy path exists.
