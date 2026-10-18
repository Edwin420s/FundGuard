# Security model and production gates

## 1. Assets to protect

- Funds and signing authority.
- Recipient wallet addresses and private recipient metadata.
- Organization membership and approval authority.
- Policy snapshots, batch hashes, and settlement evidence.
- Audit history, API credentials, database backups, and agent context.

## 2. Threats

- Prompt injection instructs the agent to bypass policy or expose secrets.
- A compromised organizer changes a recipient or amount after approval.
- A duplicate request creates a second transfer.
- Network timeout occurs after submission; retry causes a duplicate payment.
- Fake transaction hash or simulated receipt is represented as confirmed.
- Cross-tenant IDOR leaks another competition's records.
- Database operator rewrites audit rows.
- Compromised dependency, CI runner, browser session, or signing service.
- Malicious CSV payload or hostile recipient metadata enters agent context.
- Inaccurate asset decimals or implicit fiat/token conversion causes overpayment.

## 3. Required controls

- Authenticated users and tenant-aware authorization on every route.
- Separate roles and explicit approval; optional dual-control policy.
- Immutable approved proposal snapshot and approval hash comparison at execution.
- Integer base units; strict asset/network allowlist.
- Idempotency constraints and replay-safe APIs.
- Signer isolated from API and agent; transaction limits and destination policy.
- Official SDK validation and independently fetched network evidence.
- Ambiguous outcome becomes unresolved; no blind retry.
- Structured redacted logs, request IDs, rate limiting, dependency/container scanning.
- Database least privilege, backup access separation, audit external anchoring.
- CSV/input sanitization and prompt-injection-resistant tool design.
- Mainnet feature flag hard-false in buildathon deployments.

## 4. Current demo limitations

The current runnable demo is not production secure:
- No real authentication, organization tenancy, or RBAC.
- Local eligibility verification is a demo shortcut.
- Stellar address validation is minimal.
- Audit hash chain is application-level and globally serialized only by ordinary DB behavior.
- Simulation adapter generates a labelled synthetic receipt.
- No real Stellar signing/submission/verification adapter is active.
- No complete Omega SDK integration is active.
- Schema creation uses `create_all`; production must use Alembic migrations.

Do not expose this demo API to the public internet with real data or funds.

## 5. Production release gates

All must pass before live-money or mainnet enablement:
1. Independent security review and remediation of critical/high findings.
2. AuthN/RBAC/tenant isolation tests.
3. Dedicated signing/custody architecture and key-management review.
4. Tested transaction construction and network evidence verification.
5. Safe unresolved-state/reconciliation workflow.
6. Accounting ledger and reservation invariants.
7. Database migration, backup, restore, and incident drills.
8. Audit retention, external anchor, and access review.
9. Legal, privacy, and jurisdiction-specific compliance review.
10. Explicit human sign-off; mainnet toggle remains disabled until then.
