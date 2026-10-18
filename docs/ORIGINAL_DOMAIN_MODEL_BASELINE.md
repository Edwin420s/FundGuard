# Omega FundGuard --- Domain Model, Database Constraints & State Transitions

**Version:** 1.0\
**Status:** Baseline implementation design

## 1. Domain boundaries

The application is organized around these bounded domains:

1.  Identity and tenancy
2.  Programs and policy
3.  Recipients and eligibility
4.  Treasury and reservations
5.  Payout orchestration
6.  Approval and governance
7.  Settlement adapters
8.  Audit and evidence
9.  Risk and compliance
10. Agent orchestration and evaluation
11. Reporting and integrations

PostgreSQL is the authoritative store for application state. Stellar is
authoritative for the on-chain transaction outcome according to the
network's documented verification semantics. Omega memory is contextual
only and is never authoritative for balances, policy versions,
approvals, or settlement status.

## 2. Entity inventory

### Identity and tenancy

-   `users`
-   `organizations`
-   `organization_memberships`
-   `roles`
-   `permissions`
-   `role_permissions`
-   `identity_verifications`

### Program and policy

-   `competitions`
-   `funding_sources`
-   `funding_policies`
-   `funding_policy_versions`
-   `policy_evidence`

### Recipient and eligibility

-   `participants`
-   `teams`
-   `team_members`
-   `recipient_accounts`
-   `eligibility_records`
-   `eligibility_evidence`
-   `awards`

### Treasury and payout

-   `balance_snapshots`
-   `treasury_reservations`
-   `payout_batches`
-   `payouts`
-   `payout_attempts`
-   `settlement_instructions`
-   `chain_transactions`
-   `payment_receipts`
-   `reconciliation_runs`
-   `reconciliation_discrepancies`

### Governance and audit

-   `approval_requirements`
-   `approvals`
-   `audit_events`
-   `audit_anchors`
-   `evidence_references`

### Agent and integrations

-   `agent_runs`
-   `agent_tool_calls`
-   `agent_memory_records`
-   `agent_evaluations`
-   `agent_policy_versions`
-   `api_keys`
-   `webhook_endpoints`
-   `webhook_deliveries`
-   `risk_assessments`
-   `review_cases`

## 3. Key relationships

``` mermaid
erDiagram
    ORGANIZATION ||--o{ MEMBERSHIP : has
    USER ||--o{ MEMBERSHIP : joins
    ORGANIZATION ||--o{ COMPETITION : owns
    COMPETITION ||--o{ POLICY_VERSION : uses
    COMPETITION ||--o{ TEAM : registers
    TEAM ||--o{ ELIGIBILITY_RECORD : assessed_by
    COMPETITION ||--o{ PAYOUT_BATCH : contains
    POLICY_VERSION ||--o{ PAYOUT_BATCH : governs
    PAYOUT_BATCH ||--|{ PAYOUT : includes
    PAYOUT ||--o{ PAYOUT_ATTEMPT : attempts
    PAYOUT_BATCH ||--o{ APPROVAL : requires
    PAYOUT_ATTEMPT ||--o| CHAIN_TRANSACTION : produces
    CHAIN_TRANSACTION ||--o| PAYMENT_RECEIPT : verified_by
    PAYOUT_BATCH ||--o{ AUDIT_EVENT : records
    PAYOUT ||--o{ AUDIT_EVENT : records
    ORGANIZATION ||--o{ FUNDING_SOURCE : owns
```

## 4. Core entity definitions

### 4.1 Organization and membership

`organizations` - `id UUID PRIMARY KEY` - `name TEXT NOT NULL` -
`slug TEXT NOT NULL UNIQUE` - `status TEXT NOT NULL` -
`created_at TIMESTAMPTZ NOT NULL` - `updated_at TIMESTAMPTZ NOT NULL`

`organization_memberships` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL REFERENCES organizations(id)` -
`user_id UUID NOT NULL REFERENCES users(id)` -
`role_id UUID NOT NULL REFERENCES roles(id)` - `status TEXT NOT NULL` -
`created_at TIMESTAMPTZ NOT NULL` - `UNIQUE (organization_id, user_id)`

Role and permission checks are enforced by the service layer and, where
appropriate, PostgreSQL row-level security. Tenant scope must not depend
on a client-supplied organization ID alone.

### 4.2 Competition and policy version

`competitions` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL REFERENCES organizations(id)` -
`name TEXT NOT NULL` - `status TEXT NOT NULL` -
`default_network TEXT NOT NULL` - `created_at TIMESTAMPTZ NOT NULL` -
`UNIQUE (organization_id, id)`

`funding_policy_versions` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL` - `competition_id UUID NOT NULL` -
`version INTEGER NOT NULL CHECK (version > 0)` -
`status TEXT NOT NULL` - `rules JSONB NOT NULL` -
`rules_hash TEXT NOT NULL` -
`created_by UUID NOT NULL REFERENCES users(id)` -
`created_at TIMESTAMPTZ NOT NULL` - `UNIQUE (competition_id, version)` -
Composite foreign key to the competition's organization/ID should be
used where schema design supports it.

Policy versions referenced by a batch are immutable. A policy edit
creates a new version rather than updating the old version.

### 4.3 Team, recipient account, and eligibility

`teams` - `id UUID PRIMARY KEY` - `organization_id UUID NOT NULL` -
`competition_id UUID NOT NULL REFERENCES competitions(id)` -
`display_name TEXT NOT NULL` - `status TEXT NOT NULL` -
`created_at TIMESTAMPTZ NOT NULL`

`recipient_accounts` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL` -
`team_id UUID NOT NULL REFERENCES teams(id)` - `network TEXT NOT NULL` -
`address TEXT NOT NULL` - `asset_code TEXT` - `asset_issuer TEXT` -
`verification_status TEXT NOT NULL` - `created_at TIMESTAMPTZ NOT NULL`

Store public addresses only. Never store recipient private keys in this
table.

`eligibility_records` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL` - `competition_id UUID NOT NULL` -
`team_id UUID NOT NULL REFERENCES teams(id)` - `status TEXT NOT NULL` -
`policy_version_id UUID NOT NULL REFERENCES funding_policy_versions(id)` -
`evidence JSONB NOT NULL DEFAULT '{}'` -
`reviewed_by UUID REFERENCES users(id)` - `reviewed_at TIMESTAMPTZ` -
`created_at TIMESTAMPTZ NOT NULL`

Eligibility statuses should include `pending`, `verified`, `rejected`,
`incomplete`, `conflicting`, and `expired`.

### 4.4 Payout batch

`payout_batches` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL` -
`competition_id UUID NOT NULL REFERENCES competitions(id)` -
`policy_version_id UUID NOT NULL REFERENCES funding_policy_versions(id)` -
`status TEXT NOT NULL` - `currency_or_asset TEXT NOT NULL` -
`network TEXT NOT NULL` - `content_hash TEXT` - `idempotency_key TEXT` -
`created_by UUID NOT NULL REFERENCES users(id)` -
`created_at TIMESTAMPTZ NOT NULL` - `approved_at TIMESTAMPTZ` -
`executed_at TIMESTAMPTZ` - `UNIQUE (organization_id, idempotency_key)`
where key is non-null

The canonical batch hash must cover all material execution fields:
network, asset, destination, amount, payout identity, policy version,
and relevant execution constraints. Define canonical serialization and
hash algorithm explicitly and version it.

### 4.5 Payout

`payouts` - `id UUID PRIMARY KEY` - `organization_id UUID NOT NULL` -
`batch_id UUID NOT NULL REFERENCES payout_batches(id)` -
`team_id UUID NOT NULL REFERENCES teams(id)` -
`recipient_account_id UUID NOT NULL REFERENCES recipient_accounts(id)` -
`amount_base_units NUMERIC(38,0) NOT NULL CHECK (amount_base_units > 0)` -
`asset_code TEXT NOT NULL` - `asset_issuer TEXT` -
`network TEXT NOT NULL` - `destination_address TEXT NOT NULL` -
`status TEXT NOT NULL` - `obligation_key TEXT NOT NULL` -
`created_at TIMESTAMPTZ NOT NULL` -
`UNIQUE (organization_id, obligation_key)`

For Stellar native XLM, one XLM equals 10,000,000 stroops. Use integer
base units for authoritative XLM arithmetic. Other assets must define
their precision and canonical representation explicitly.

`obligation_key` identifies the business obligation (for example,
competition + award round + team + award type). It should prevent
accidental duplicate obligations, but the schema must still permit a
documented new obligation when policy authorizes it.

### 4.6 Approval

`approvals` - `id UUID PRIMARY KEY` - `organization_id UUID NOT NULL` -
`batch_id UUID NOT NULL REFERENCES payout_batches(id)` -
`approver_user_id UUID NOT NULL REFERENCES users(id)` -
`approved_content_hash TEXT NOT NULL` - `decision TEXT NOT NULL` -
`reason TEXT` - `created_at TIMESTAMPTZ NOT NULL` -
`revoked_at TIMESTAMPTZ`

Allowed decisions: `approved`, `rejected`, `amendment_requested`.
Enforce authorization, separation-of-duties rules, and required approver
count in the service layer. An approval is valid only if its hash
matches the current canonical batch hash and policy requirements are
satisfied.

### 4.7 Payout attempts and chain transactions

`payout_attempts` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL` -
`payout_id UUID NOT NULL REFERENCES payouts(id)` -
`attempt_number INTEGER NOT NULL CHECK (attempt_number > 0)` -
`idempotency_key TEXT NOT NULL` - `status TEXT NOT NULL` -
`submitted_at TIMESTAMPTZ` - `completed_at TIMESTAMPTZ` -
`failure_code TEXT` - `failure_detail TEXT` -
`UNIQUE (payout_id, attempt_number)` -
`UNIQUE (organization_id, idempotency_key)`

`chain_transactions` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL` -
`payout_attempt_id UUID NOT NULL REFERENCES payout_attempts(id)` -
`network TEXT NOT NULL` - `transaction_hash TEXT` -
`ledger_or_block_reference TEXT` - `network_success BOOLEAN` -
`verification_status TEXT NOT NULL` - `observed_at TIMESTAMPTZ` -
`UNIQUE (network, transaction_hash)` where hash is non-null

`payment_receipts` - `id UUID PRIMARY KEY` -
`chain_transaction_id UUID NOT NULL REFERENCES chain_transactions(id)` -
`receipt_payload JSONB NOT NULL` - `receipt_hash TEXT NOT NULL` -
`verified_at TIMESTAMPTZ NOT NULL` - `verification_method TEXT NOT NULL`

Receipt payloads should contain only required evidence and avoid
sensitive personal data.

### 4.8 Audit event

`audit_events` - `id UUID PRIMARY KEY` -
`organization_id UUID NOT NULL` - `event_type TEXT NOT NULL` -
`actor_type TEXT NOT NULL` - `actor_id TEXT` -
`entity_type TEXT NOT NULL` - `entity_id UUID NOT NULL` -
`correlation_id UUID NOT NULL` - `occurred_at TIMESTAMPTZ NOT NULL` -
`payload JSONB NOT NULL` - `previous_event_hash TEXT` -
`event_hash TEXT NOT NULL`

Use restricted database permissions to prevent ordinary application
roles from updating or deleting audit events. Hash chaining should be
deterministic and versioned. Periodic external/on-chain anchoring can
make later modification more detectable, but does not prove the truth of
the original event.

## 5. Database invariants

1.  All organization-owned entities have a tenant identifier and
    authorized parent relationship.
2.  Policy versions are immutable after creation.
3.  Approved batch material fields cannot change without invalidating
    approval.
4.  A batch cannot execute unless all required approvals match its
    current content hash.
5.  Amounts must be positive and represented in exact units.
6.  The same idempotency key cannot create multiple execution attempts
    for the same scoped operation.
7.  One obligation cannot be settled twice.
8.  Network transaction hashes are unique within their network.
9.  A payout is not confirmed until the corresponding transaction and
    payment details are independently verified.
10. Unknown transaction outcomes are not treated as failures eligible
    for immediate resubmission.
11. Reservations and available balances are updated transactionally.
12. A batch can be partially complete; each payout has an independent
    state.
13. Audit records are append-only for ordinary application roles.
14. Tenant-scoped reads and writes are authorized server-side.
15. Deletion of records referenced by financial or audit history is
    restricted; use archival/tombstone policies instead.

## 6. State machines

### 6.1 Payout batch

States: - `draft` - `validating` - `proposed` - `pending_approval` -
`approved` - `executing` - `partially_completed` - `completed` -
`rejected` - `cancelled` - `reconciliation_required`

Key transitions: - `draft -> validating`: request validation. -
`validating -> proposed`: all blocking checks pass. -
`validating -> draft`: correctable validation failures. -
`validating -> rejected`: irrecoverable policy violation or explicit
rejection. - `proposed -> pending_approval`: proposal is frozen and
hashed. - `pending_approval -> approved`: required valid approvals are
present. - `pending_approval -> rejected`: authorized rejection. -
`approved -> executing`: execution service revalidates policy, hash,
approvals, reservations, and idempotency. - `executing -> completed`:
every payout is confirmed. - `executing -> partially_completed`: some
payouts confirmed and others failed/unresolved. -
`executing -> reconciliation_required`: at least one outcome is
uncertain. - `partially_completed -> completed`: remaining payouts
settle or are explicitly resolved according to policy. - Any
pre-execution state may be cancelled if permissions and policy allow. -
Material edits create a new batch version or invalidate the previous
approval; never mutate an approved intent silently.

### 6.2 Individual payout

States: - `draft` - `validated` - `awaiting_approval` - `approved` -
`submitting` - `submitted` - `confirming` - `confirmed` - `failed` -
`unknown` - `cancelled` - `manual_review`

Rules: - `unknown` requires reconciliation before a retry. - `failed`
requires a definitive failure result or a reviewed recovery decision. -
`confirmed` is terminal for that attempt/obligation unless a separate
correction or reversal process is explicitly supported. - One failed
payout does not change another payout's confirmed status.

### 6.3 Settlement attempt

States: - `prepared` - `signed` - `submitted` - `accepted_pending` -
`confirmed_success` - `confirmed_failure` - `unknown` -
`abandoned_before_submission`

A timeout after submission is `unknown`, not automatically `failed`.
Before retry, query the network using the transaction reference or other
supported reconciliation mechanism.

### 6.4 Approval

States: - `pending` - `approved` - `rejected` - `amendment_requested` -
`expired` - `revoked`

An approval only authorizes the content hash it explicitly references.
Any change to recipient, amount, asset, network, or other material field
invalidates it.

## 7. Treasury accounting model

Track separate amounts: - `available` - `reserved` -
`submitted_or_unresolved` - `confirmed_paid` -
`outstanding_obligations` - `policy_reserve` - `fees_paid` -
`reconciliation_difference`

A simplified invariant is:

`accounted_funds = available + reserved + submitted_or_unresolved + confirmed_paid + other explicitly categorized amounts`

The exact equation depends on whether categories overlap in the
implementation. Define one accounting model with mutually exclusive
buckets and test conservation after every event. Do not double-count
unresolved payments as both reserved and paid.

Reservations should be created and released transactionally. If balance
data is stale or a network result is uncertain, the system should
conservatively hold the obligation from being reused until
reconciliation resolves it.

## 8. Canonical batch hash

Define a versioned canonical JSON representation containing: - batch ID
and batch schema version - organization and competition IDs - policy
version and policy hash - network and asset - ordered payout entries -
each payout ID, recipient address, exact amount, asset identifier, and
obligation key - applicable fee and reserve assumptions - expiration or
validity constraints where used

Canonicalization must specify stable key ordering, string normalization,
integer amount formatting, and excluded volatile fields such as
display-only labels. Hash the canonical bytes using SHA-256. Store the
canonicalization version alongside the hash.

The hash is a commitment to the exact proposal; it is not itself proof
that the proposal is lawful or correct.

## 9. Migration and implementation notes

-   Use Alembic migrations for schema changes.
-   Add foreign keys, unique constraints, check constraints, and indexes
    through migrations.
-   Index organization ID, competition ID, batch status, payout status,
    created timestamp, correlation ID, and transaction hash as
    appropriate.
-   Consider PostgreSQL row-level security as defense in depth, not as a
    replacement for application authorization.
-   Use database transactions and appropriate locking for reservations,
    approvals, and execution transitions.
-   Store large evidence files outside the relational database where
    appropriate, with access-controlled references and integrity hashes.
-   Do not store signing secrets in PostgreSQL.
-   Include seed data for a complete synthetic competition and
    reproducible tests.
