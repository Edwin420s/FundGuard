# Domain model, constraints, and state transitions

## 1. Entities

| Entity | Purpose | Key constraints |
|---|---|---|
| Organization | Tenant boundary | Every production business object is scoped to an organization |
| Membership | User, organization, role | Unique `(organization_id, user_id)`; revocation is auditable |
| Competition | A program/hackathon | Status lifecycle; network allowlist |
| PolicyVersion | Immutable policy snapshot | Unique version per competition; canonical hash |
| Recipient | Team/person receiving award | Eligibility state and destination validation; unique destination policy |
| EligibilityDecision | Review and evidence | Reviewer, decision, timestamp, evidence reference |
| FundingAccount | Asset/network balance view | Never conflate fiat valuation and token units |
| Reservation | Amount committed to approved obligations | Non-negative, asset/network-scoped |
| PayoutBatch | Immutable proposed allocation | Canonical content hash, policy version, idempotency key |
| Payout | One recipient transfer obligation | Integer base units; independent state and evidence |
| Approval | Human authorization | Must bind to exact batch hash and actor/role |
| SettlementAttempt | Network submission attempt | Unique attempt/idempotency identifier; store outcome class |
| Receipt | Verified network evidence | Network, transaction hash, operation details, verifier timestamp |
| AuditEvent | Append-only activity record | Hash chain; actor, correlation ID, event time, details |
| AgentRun | Omega workflow execution | Prompt/context/tool/result metadata; tenant scope |
| AgentToolCall | One constrained tool call | Tool name/version, validated arguments, result/error |
| ReconciliationCase | Uncertain/failed outcome | Owner, evidence, resolution, timestamps |
| ExportJob | Audit/report generation | Scope, requester, artifact hash, expiry/access policy |

The current runnable demo implements Competition, Recipient, PayoutBatch, Payout, and AuditEvent. The remaining entities are part of the complete target model and must be added through migrations before production deployment.

## 2. Key relationships

- Organization 1:N Competition.
- Competition 1:N PolicyVersion, Recipient, PayoutBatch, AuditEvent.
- PolicyVersion 1:N PayoutBatch references (version snapshots remain immutable).
- PayoutBatch 1:N Payout and 1:N Approval/SettlementAttempt.
- Payout N:1 Recipient.
- Payout 1:N SettlementAttempt and 0:1 verified Receipt (multiple attempts may exist only under safe retry rules).
- AgentRun 1:N AgentToolCall.
- ReconciliationCase links an unresolved payout and all evidence considered.

## 3. Important database constraints

1. Monetary values are integers in base units or exact decimal strings; never floating point.
2. All amounts are non-negative; transfer amount is strictly positive.
3. Unique idempotency constraint per tenant and operation scope.
4. Unique competition + recipient destination where duplicate destinations are prohibited.
5. `approval.batch_hash == payout_batch.content_hash` is required before execution.
6. Once a batch is approved, its content is immutable; any edit produces a new batch.
7. A payout cannot be `confirmed` without a verified receipt and expected operation match.
8. A payout with ambiguous submission outcome cannot be retried before reconciliation.
9. `available = observed_balance - reserved - pending_outgoing - required_minimum_reserve`, with asset and network dimensions matching.
10. Batch totals must equal the sum of its payout amounts.
11. Each audit event includes prior hash and its own canonical event hash.
12. Tenant scope must be checked on every query and mutation.
13. Database constraints are backed by domain-level validation and tests; application checks alone are insufficient for uniqueness and concurrent requests.

## 4. Batch state machine

```text
proposed -> approved -> executing -> confirmed
    |          |           |          ^
    |          |           +-> partially_confirmed
    |          |           +-> unresolved
    |          |           +-> failed
    |          +-> cancelled
    +-> cancelled

simulated is a distinct demo terminal state, never equivalent to confirmed.
```

## 5. Payout state machine

```text
proposed -> authorized -> submitted -> confirmed
                              |  |        |
                              |  +-> failed (only with verified failure evidence)
                              +----> unresolved (ambiguous timeout/response)
unresolved -> confirmed (reconciliation finds matching successful operation)
unresolved -> failed (reconciliation proves no successful operation and policy permits)
unresolved -> manual_review (evidence conflict or cannot establish outcome)
```

`simulated` is separate from the real settlement state machine.

## 6. Accounting definitions

- **Allocated:** sum of proposed award obligations.
- **Reserved:** funding held against approved but unsettled obligations.
- **Submitted/pending:** transfer request submitted, outcome not yet confirmed.
- **Paid/confirmed:** sum of payouts with independently verified matching operations.
- **Outstanding:** approved obligation not confirmed paid.
- **Unresolved:** amount whose actual network outcome is not known.
- **Carry-forward reserve:** amount intentionally not allocated in this cycle.
- **Available:** observed on-chain balance minus reservations, pending outflow, and configured minimum reserve.

Do not count an unresolved amount as available. Do not release a reservation until a payout reaches a resolved terminal state.

## 7. Canonical content hash

Canonical proposal includes competition, policy version, network, asset, ordered recipient IDs/destinations, integer amounts, reserve, and relevant rule snapshot. Canonical JSON uses stable key ordering and normalized strings. Hash uses SHA-256. The approver sees the hash and human-readable proposal; approval stores the exact hash. Changing any hashed field invalidates approval.

## 8. Audit integrity caveat

Hash-linked audit events help detect changes but do not make a database administrator unable to rewrite the entire chain. Production requires restricted database access, backups, independent export/anchor, and documented retention.
