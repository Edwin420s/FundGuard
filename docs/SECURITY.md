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
- Mainnet feature flag hard-false in sandbox and testing deployments.

## 4. Operational Boundaries and Controls

The platform implements strict defense-in-depth measures:
- Multi-tenant organization boundaries and JWT-authenticated session security.
- Cryptographic SHA-256 hash chaining per workspace with tamper-detection verification.
- Strict ed25519 StrKey public key validation preventing malformed or invalid addresses.
- Dual-control governance: Payout batches require explicit human authorization matching the canonical proposal SHA-256 fingerprint.
- Multi-engine settlement architecture: Simulated dry-run mode and real Stellar Testnet adapter with independent Horizon transaction verification.
- Solvency conservation invariant: Total budget equals confirmed payouts plus pending authorizations plus available funds and reserves.
- Testnet and simulation isolation: Mainnet execution is strictly disabled. Production deployment requires dedicated hardware security modules (HSM) or custody integration.

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
