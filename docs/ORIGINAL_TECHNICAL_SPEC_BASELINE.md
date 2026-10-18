# Omega FundGuard --- Technical Implementation Specification

**Version:** 1.0\
**Status:** Baseline API and implementation contract\
**API prefix:** `/api/v1`

## 1. Reference stack

-   Frontend: React + Vite.
-   Backend API: Python + FastAPI.
-   Database: PostgreSQL.
-   Migrations: Alembic.
-   Agent: SingularityNET Omega / Hyperon / MeTTa, connected through a
    version-specific adapter.
-   Settlement: Stellar SDK and supported Stellar network APIs.
-   Async work: background worker and queue for reconciliation,
    notifications, and long-running jobs.
-   Testing: Pytest, HTTP integration tests, database integration tests,
    agent evaluations, and testnet smoke tests.
-   Deployment: Docker-based local development; production deployment
    and secret storage selected separately.

Exact Omega, Raven, and Stellar SDK APIs must be verified against the
current official repositories and documentation during implementation.
Do not invent an integration endpoint or assume a tool has
transaction-signing authority.

## 2. Service boundaries

### API application

Authenticates requests, validates schemas, enforces tenant scope,
creates workflow commands, and returns application state.

### Domain services

Implement policies, allocation calculations, approvals, reservations,
payout state transitions, and audit event creation. Domain services must
be callable without an LLM.

### Omega adapter

Maps Omega tool calls to constrained application commands and converts
domain results into structured outputs. It must not expose database
credentials, signing keys, arbitrary shell access, or unrestricted
transaction construction.

### Settlement adapter

Validates network and asset parameters, prepares a transaction, invokes
the protected signer, submits the transaction, and verifies the
resulting payment evidence.

### Worker

Runs bounded asynchronous tasks such as reconciliation, webhook
delivery, export generation, and scheduled monitoring. Tasks must be
idempotent and resumable.

### Audit service

Writes append-only events with correlation IDs, actor metadata, and
evidence references. It must not be able to silently modify prior
financial events.

## 3. API conventions

-   JSON request/response bodies.
-   UUIDs for internal IDs.
-   UTC timestamps in ISO 8601 format.
-   Versioned routes under `/api/v1`.
-   Authenticated organization scope derived from the identity/session
    and checked against resource ownership.
-   Standard error envelope:
    `{"error":{"code":"...","message":"...","request_id":"..."}}`
-   Pagination for list endpoints using a cursor or limit/offset with
    documented ordering.
-   Idempotency keys for commands that create or execute financial
    obligations.
-   No private keys, secret seeds, or credentials in API payloads or
    logs.
-   Return `202 Accepted` for genuinely asynchronous commands, with a
    resource/status URL.
-   Do not return `confirmed` until network evidence has been verified.

## 4. API contracts

These contracts define the intended interface; request and response
examples are illustrative.

### 4.1 Create competition

`POST /competitions`

Request:

``` json
{
  "name": "FundGuard Demo Challenge",
  "description": "Synthetic buildathon payout scenario",
  "default_network": "stellar-testnet"
}
```

Success: `201 Created`

Response:

``` json
{
  "id": "UUID",
  "name": "FundGuard Demo Challenge",
  "status": "draft",
  "default_network": "stellar-testnet",
  "created_at": "2026-10-23T10:00:00Z"
}
```

Acceptance: - Competition is associated with the authenticated
organization. - Unsupported networks are rejected. - Another
organization cannot access the competition.

### 4.2 Create policy version

`POST /competitions/{competition_id}/policies`

Request:

``` json
{
  "release_rule": {
    "type": "eligible_ratio",
    "target_eligible_count": 50,
    "minimum_eligible_count": 1
  },
  "total_fund": {
    "amount": "1700.00",
    "currency": "USD"
  },
  "award_rules": [
    {"category": "winner", "amount": "1000000", "unit": "stroops"}
  ],
  "reserve_rule": {"type": "carry_forward"},
  "eligibility_requirements": ["organizer_verified"]
}
```

The example mixes illustrative fiat fund metadata and a testnet asset
amount only to demonstrate schema concepts; the production schema must
model fiat valuation and blockchain asset units separately. Never
silently convert USD to XLM.

Success: `201 Created`

Acceptance: - Invalid or contradictory rules are rejected. - Policy
version and hash are created. - Editing creates a new version. -
Existing approved batches retain their referenced policy version.

### 4.3 Register a team

`POST /competitions/{competition_id}/teams`

Request:

``` json
{
  "display_name": "Team Northstar",
  "recipient": {
    "network": "stellar-testnet",
    "address": "G..."
  },
  "eligibility_status": "pending"
}
```

Success: `201 Created`

Acceptance: - Address format and network are validated. - Eligibility
cannot be set to verified without the configured evidence/review
process. - Sensitive data is not written to public-chain records.

### 4.4 Generate a payout batch

`POST /competitions/{competition_id}/batches`

Headers:

``` text
Idempotency-Key: <unique-client-generated-key>
```

Request:

``` json
{
  "policy_version_id": "UUID",
  "team_ids": ["UUID", "UUID"],
  "asset": {
    "network": "stellar-testnet",
    "type": "native",
    "code": "XLM"
  },
  "mode": "propose_only"
}
```

Success: `201 Created`

Response:

``` json
{
  "id": "UUID",
  "status": "proposed",
  "policy_version_id": "UUID",
  "content_hash": "sha256:<hash>",
  "totals": {
    "recipient_count": 2,
    "total_amount_base_units": "2000000",
    "reserve_base_units": "8000000"
  },
  "validation": {
    "passed": true,
    "blocking_errors": [],
    "warnings": []
  }
}
```

The amounts above are sample base-unit values, not fiat values. The
reserve calculation must be derived from a single defined asset/balance
model.

Acceptance: - Allocation is calculated deterministically. - Policy and
eligibility are checked. - Canonical batch content and hash are
stored. - No transfer is submitted during proposal creation. - Duplicate
create requests with the same idempotency key do not create duplicate
obligations.

### 4.5 Validate batch

`POST /batches/{batch_id}/validate`

Success: `200 OK`

Response:

``` json
{
  "batch_id": "UUID",
  "valid": true,
  "policy_version_id": "UUID",
  "content_hash": "sha256:<hash>",
  "checks": [
    {"code": "ELIGIBILITY_VALID", "passed": true},
    {"code": "FUNDING_CAP_VALID", "passed": true},
    {"code": "RECIPIENTS_VALID", "passed": true},
    {"code": "NO_DUPLICATE_OBLIGATIONS", "passed": true}
  ]
}
```

Acceptance: - Validation results are reproducible. - Blocking violations
prevent progression to approval. - Warnings are visible and have defined
severity.

### 4.6 Approve or reject batch

`POST /batches/{batch_id}/approvals`

Request:

``` json
{
  "decision": "approved",
  "approved_content_hash": "sha256:<exact-batch-hash>",
  "reason": "Reviewed award amounts and recipients"
}
```

Success: `201 Created`

Acceptance: - The approver is authenticated and authorized. - The
submitted hash matches the current batch. - Required
separation-of-duties and approval thresholds are satisfied. - Rejected
and amendment-requested outcomes are recorded. - A material change after
approval invalidates approval.

### 4.7 Execute batch

`POST /batches/{batch_id}/execute`

Headers:

``` text
Idempotency-Key: <unique-execution-key>
```

Request:

``` json
{
  "approved_content_hash": "sha256:<exact-approved-hash>"
}
```

Success: `202 Accepted` if asynchronous; return a status URL.

Response:

``` json
{
  "batch_id": "UUID",
  "status": "executing",
  "status_url": "/api/v1/batches/UUID"
}
```

Acceptance: - The backend revalidates approval, policy, content hash,
recipient, amount, available balance, and idempotency. - Mainnet is
rejected unless explicitly enabled through production release
controls. - Signing secrets are never passed to the agent. - A duplicate
request returns the existing operation status and does not create a
second transfer. - Submission outcomes are verified independently.

### 4.8 Retrieve payout and receipt

`GET /payouts/{payout_id}`

Response:

``` json
{
  "id": "UUID",
  "status": "confirmed",
  "network": "stellar-testnet",
  "asset": {"type": "native", "code": "XLM"},
  "amount_base_units": "1000000",
  "transaction": {
    "hash": "<verified-hash>",
    "network_success": true,
    "payment_matches_expected": true,
    "verified_at": "2026-10-23T11:00:00Z"
  }
}
```

The sample is a schema illustration. Never fabricate a transaction hash
or mark an unverified transaction as confirmed.

### 4.9 Reconcile payout

`POST /payouts/{payout_id}/reconcile`

Acceptance: - Queries the appropriate network evidence using supported
APIs. - Records the reconciliation attempt and outcome. - Resolves a
payout only when evidence is sufficient. - Leaves the state unknown and
escalates if evidence is inconclusive. - Does not blindly resubmit an
uncertain transfer.

### 4.10 Audit history

`GET /batches/{batch_id}/audit?event_type=...&cursor=...`

Acceptance: - Results are scoped to the caller's authorized
organization. - Events are ordered deterministically. - Each event
includes actor, time, correlation ID, event type, and evidence
references. - Exports preserve original event timestamps and integrity
metadata.

### 4.11 Agent run

`POST /agent/runs`

Request:

``` json
{
  "competition_id": "UUID",
  "intent": "prepare_payout_proposal",
  "context": {
    "batch_id": "UUID"
  }
}
```

Response:

``` json
{
  "agent_run_id": "UUID",
  "status": "completed",
  "summary": "Proposal prepared and validated; awaiting human approval.",
  "tool_calls": [
    {"tool": "get_funding_policy", "status": "success"},
    {"tool": "get_eligible_teams", "status": "success"},
    {"tool": "calculate_allocation", "status": "success"},
    {"tool": "validate_payout_batch", "status": "success"}
  ],
  "next_action": "human_approval_required"
}
```

Acceptance: - The agent run is tied to an authenticated organization and
permitted resources. - Tool calls are schema validated and permission
checked. - Agent memory does not override current policy or state. - An
agent run cannot execute a payout merely because the user asks it in
natural language; execution still passes through the approved command
and authorization boundary.

## 5. Omega tool contracts

Each tool should have a strict input schema, output schema, permission
requirement, side-effect classification, timeout, and error contract.

  ---------------------------------------------------------------------------
  Tool                        Side effect             Required control
  --------------------------- ----------------------- -----------------------
  `get_funding_policy`        Read                    Tenant-scoped
                                                      authorization

  `get_eligible_teams`        Read                    Policy/version
                                                      reference

  `calculate_allocation`      Pure computation        Deterministic inputs
                                                      and output

  `validate_payout_batch`     Read/validation         Explicit validation
                                                      result

  `request_human_approval`    Workflow write          Authenticated organizer
                                                      context

  `get_approval_status`       Read                    Batch access
                                                      authorization

  `execute_approved_payout`   Financial side effect   Exact approval hash,
                                                      idempotency, backend
                                                      authorization

  `verify_transaction`        Read                    Network evidence
                                                      validation

  `get_audit_history`         Read                    Tenant and role
                                                      authorization

  `reconcile_payout`          Controlled workflow     Reconciliation
                              write                   permissions and audit
                                                      event
  ---------------------------------------------------------------------------

The model cannot grant itself permissions. Tools that can change state
must enforce all controls server-side.

## 6. Transaction execution algorithm

1.  Receive execution command and idempotency key.
2.  Begin database transaction and lock the relevant batch/obligations.
3.  Verify batch state, current canonical hash, policy version,
    approvals, recipient/asset/network fields, limits, and reservations.
4.  If the operation already exists for the idempotency key, return its
    state.
5.  Persist a payout attempt and outbox/job record atomically.
6.  Commit the database transaction.
7.  Worker constructs and submits the network transaction through the
    settlement adapter and protected signing boundary.
8.  Persist transaction reference and submission evidence.
9.  Independently query network status and matching payment operation.
10. Mark confirmed only when verification rules pass.
11. If submission outcome is uncertain, mark unknown and reconcile
    before retry.
12. Append audit events for each material transition.
13. Update treasury reservations and reconciliation figures
    transactionally.

Because the database and blockchain do not share one atomic transaction,
use an outbox/worker pattern and explicit reconciliation rather than
pretending the operation is globally atomic.

## 7. Error contract

Use stable machine-readable error codes, for example: -
`AUTHENTICATION_REQUIRED` - `FORBIDDEN` - `RESOURCE_NOT_FOUND` -
`TENANT_SCOPE_VIOLATION` - `POLICY_INVALID` - `ELIGIBILITY_INCOMPLETE` -
`ALLOCATION_EXCEEDS_LIMIT` - `INSUFFICIENT_AVAILABLE_BALANCE` -
`APPROVAL_REQUIRED` - `APPROVAL_HASH_MISMATCH` -
`IDEMPOTENCY_CONFLICT` - `INVALID_RECIPIENT_ADDRESS` -
`UNSUPPORTED_NETWORK` - `SETTLEMENT_OUTCOME_UNKNOWN` -
`TRANSACTION_VERIFICATION_FAILED` - `RECONCILIATION_REQUIRED` -
`RATE_LIMITED` - `INTERNAL_ERROR`

Do not return signing details, private keys, stack traces, or sensitive
provider responses to clients.

## 8. Test strategy and acceptance criteria

### Unit tests

-   Allocation calculations for fixed, ranked, and proportional
    policies.
-   Reserve calculations and precision.
-   Policy schema validation.
-   Batch canonicalization and stable hash.
-   State transition legality.
-   Idempotency-key handling.
-   Approval hash invalidation.
-   Risk-rule decisions.
-   Audit event hashing.

### Database integration tests

-   Foreign-key and uniqueness constraints.
-   Tenant isolation.
-   Concurrent reservation attempts.
-   Duplicate execution requests.
-   Transactional state transitions.
-   Append-only audit permissions.
-   Migration upgrade and downgrade behavior where supported.

### API integration tests

-   Competition creation and access control.
-   Policy version creation.
-   Team and recipient validation.
-   Batch proposal and validation.
-   Approval/rejection flow.
-   Execute-before-approval rejection.
-   Execution with stale approval rejection.
-   Audit filtering and export authorization.

### Agent evaluation tests

-   Correct tool selection for payout preparation.
-   Requests for clarification when policy or recipient data is missing.
-   Refusal to bypass approval.
-   Resistance to prompt injection in external records.
-   No invented balances, eligibility, transaction hashes, or success
    claims.
-   Correct response when a tool fails or returns conflicting data.
-   Memory cannot override a new policy version.
-   Tool-call trace contains sufficient evidence for review.

### Stellar testnet integration tests

-   Submit a small configured testnet payment.
-   Retrieve the transaction result and relevant payment operation.
-   Verify destination, asset, amount, and success status.
-   Simulate timeout/unknown response and reconcile before retry.
-   Verify a repeated request cannot cause a duplicate payment.
-   Verify insufficient balance and invalid recipient errors are
    handled.
-   Preserve a real transaction hash in the audit record.

### Security tests

-   Cross-tenant read/write attempts are rejected.
-   Unauthorized approval is rejected.
-   Approval by a user who cannot approve their own proposal is rejected
    where separation of duties is configured.
-   Batch modification after approval blocks execution.
-   Secret material does not appear in agent inputs, logs, traces, API
    responses, or source control.
-   Arbitrary agent-generated transactions are rejected.
-   Mainnet configuration remains disabled by default.
-   Rate limits and webhook signature/replay checks behave as specified.

## 9. Definition of done by capability

A capability is complete only when: 1. Its domain behavior is
implemented. 2. Its API or internal contract is documented. 3. Its
authorization and failure behavior are defined. 4. Unit and integration
tests pass. 5. Audit behavior is implemented. 6. Operational limitations
are documented. 7. A reproducible test or demo proves the behavior.

A UI mock, a successful API response without verified side effects, or
an LLM explanation alone does not satisfy completion.

## 10. Initial end-to-end release gate

The first complete vertical release must demonstrate:

1.  Create a competition and activate a policy.
2.  Register synthetic eligible winners and testnet recipients.
3.  Use Omega to retrieve policy and teams and call the deterministic
    calculator.
4.  Produce a validated, hashed multi-recipient proposal.
5.  Reject execution before approval.
6.  Approve the exact proposal using an authenticated user.
7.  Submit at least one real Stellar testnet transfer.
8.  Verify the transaction and matching payment operation independently.
9.  Record the receipt and audit timeline.
10. Demonstrate duplicate-request protection and safe reconciliation of
    a failed or unresolved case.

This establishes a real foundation for the broader product without
falsely claiming that production financial operations are ready.
