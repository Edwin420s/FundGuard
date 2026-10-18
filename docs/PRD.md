# Product Requirements Document — Omega FundGuard

**Version:** 1.1 · **Primary user:** hackathon organizers · **Initial settlement target:** Stellar testnet

## 1. Summary

Omega FundGuard coordinates funding rules, recipient eligibility, payout allocation, human approval, settlement, receipt verification, reconciliation, and audit reporting. It targets hackathons first and can extend to accelerators, grant programs, fellowships, community treasuries, and prize competitions.

Omega provides context retrieval and workflow orchestration. Deterministic services remain authoritative for eligibility state, amount arithmetic, policy enforcement, permissions, idempotency, approvals, and settlement state. The agent cannot sign transactions or mark payments confirmed.

## 2. Problem

Prize disbursement often spans spreadsheets, forms, chat, wallet addresses, and transaction explorers. These fragmented workflows make it difficult to establish which policy version was applied, why a recipient was eligible, who approved an allocation, whether a transaction really settled, and how much remains outstanding or reserved.

## 3. Personas

- **Organizer:** creates competition, recipient list, award rules, and proposed batches.
- **Finance approver:** reviews totals, reserve, recipient destinations, and batch hash; explicitly approves.
- **Operations administrator:** manages membership, integrations, incidents, reconciliation, and exports.
- **Recipient:** views permitted status and receipt information.
- **Auditor/reviewer:** verifies the relationship between policy, proposal, approval, settlement evidence, and reconciliation.

## 4. Product principles

1. Human accountability for financial actions.
2. Deterministic money and policy logic.
3. Evidence-grounded agent explanations.
4. Traceable material actions with actor, time, correlation ID, and evidence.
5. Network adapters isolated from business workflows.
6. Secrets never exposed to the LLM.
7. Explicit distinctions among proposed, approved, submitted, confirmed, failed, simulated, and unresolved.
8. Full product design with incremental milestones; no claim that a milestone is complete until acceptance tests pass.

## 5. Goals

- Versioned funding policy and eligibility rules.
- Recipient register with explicit review.
- Deterministic allocation and reserve calculations.
- Batch proposal with canonical content hash.
- Approval bound to exact hash and policy version.
- Stellar testnet transfer execution through a protected adapter.
- Independent verification of transaction and payment-operation evidence.
- Duplicate prevention and safe handling of ambiguous outcomes.
- Application audit log and public-verifiable receipt references.
- Dashboard, API, reports, operational monitoring, and agent-assisted workflows.
- Multi-organization tenancy and role-based access before production.

## 6. Non-goals for the buildathon release

- Mainnet or live-money transfer.
- Unverified cross-chain bridge.
- Regulatory-compliance claims without jurisdiction-specific review.
- LLM as financial source of truth.
- Public-chain storage of private recipient information.
- Unrestricted agent shell access, key access, or transaction signing.

## 7. Functional requirements

### Identity, tenancy, and governance
- **FR-001 MUST:** every business record belongs to an organization or competition scope.
- **FR-002 MUST:** production identity is authenticated and all reads/writes enforce tenant scope.
- **FR-003 MUST:** role-based permissions separate organizer, reviewer, approver, operator, and auditor.
- **FR-004 MUST:** high-impact actions record the initiating human and the approving human; separation-of-duties policy is configurable.
- **FR-005 SHOULD:** invite, suspend, and revoke organization members; rotate sessions and API credentials.

### Competitions and recipients
- **FR-010 MUST:** create, edit, pause, and archive competitions with a documented lifecycle.
- **FR-011 MUST:** register recipient identity metadata and destination address without publishing private personal data on-chain.
- **FR-012 MUST:** new recipients start pending; eligibility requires a recorded review/evidence decision.
- **FR-013 MUST:** duplicate destination handling is explicit and competition-scoped.
- **FR-014 SHOULD:** support CSV import with preview, validation, row-level errors, and rollback.
- **FR-015 SHOULD:** maintain eligibility history and evidence references.

### Policies and allocation
- **FR-020 MUST:** funding policies are versioned and immutable once referenced by an approved batch.
- **FR-021 MUST:** use integer base units for blockchain amounts; never use binary floating point for money.
- **FR-022 MUST:** keep fiat valuation and on-chain asset units separate; no implicit USD/XLM conversion.
- **FR-023 MUST:** calculate released amount, awards, reserved amount, and carry-forward deterministically.
- **FR-024 MUST:** disclose exclusions, rounding, fee assumptions, caps, and unmet conditions.
- **FR-025 SHOULD:** policy simulator compares scenarios before publication.

### Batch, approval, and settlement
- **FR-030 MUST:** batch proposal contains recipients, destination, amount, asset/network, policy version, totals, reserve, and content hash.
- **FR-031 MUST:** use idempotency keys for commands that create financial obligations.
- **FR-032 MUST:** approval is bound to exact canonical content hash; any change requires a new proposal and approval.
- **FR-033 MUST:** revalidate eligibility, permissions, policy, balance, and approval immediately before execution.
- **FR-034 MUST:** execution is testnet-only in this release and disabled unless explicitly configured.
- **FR-035 MUST:** independently verify transaction and payment operation before marking a real payout confirmed.
- **FR-036 MUST:** partial success is represented per payout; batch status is derived from child payout states.
- **FR-037 MUST:** uncertain outcome is unresolved and reconciled before retry.
- **FR-038 SHOULD:** fee/balance preflight, timeouts, network retry policy, and failure categorization.
- **FR-039 SHOULD:** support resumable reconciliation and operator resolution with evidence.

### Audit and reporting
- **FR-040 MUST:** append structured events for policy changes, eligibility decisions, proposal, approval, execution attempt, receipt, failure, reconciliation, and export.
- **FR-041 MUST:** event records include actor, timestamp, correlation ID, entity reference, event details, and integrity hash.
- **FR-042 MUST:** audit exports filter by competition, date, actor, batch, and outcome.
- **FR-043 SHOULD:** export CSV/JSON and a human-readable evidence report.
- **FR-044 SHOULD:** verify receipt links and audit integrity on demand.
- **FR-045 MUST:** label simulated evidence clearly; it cannot be represented as a network transaction.

### Omega agent
- **FR-050 MUST:** agent calls only allowlisted, typed domain tools.
- **FR-051 MUST:** agent may explain, gather evidence, draft proposals, and report outcomes; it cannot bypass human approval.
- **FR-052 MUST:** tool outputs are structured, attributable, and persisted with agent run/correlation identifiers.
- **FR-053 MUST:** agent memory is scoped, inspectable, and cannot silently override policy.
- **FR-054 SHOULD:** evaluation suite tests hallucinated receipts, prompt injection, conflicting policy, ambiguous settlement, and unsafe retries.

### Product quality
- **FR-060 MUST:** accessible keyboard-usable UI with clear loading/error/empty states.
- **FR-061 MUST:** API has versioned routes, validated schemas, documented errors, and health checks.
- **FR-062 MUST:** tests cover policy arithmetic, transitions, idempotency, approval hash, and settlement verification.
- **FR-063 SHOULD:** metrics, alerting, backup/restore, rate limiting, and operational runbooks.
- **FR-064 MUST:** deployment and documentation state exactly which integrations are real versus simulated.

## 8. Non-functional requirements

- **Security:** least privilege; secrets manager for signer keys; dependency scanning; strict CORS; TLS; authenticated endpoints; immutable external audit anchor recommended for production.
- **Correctness:** integer arithmetic, canonical hashing, transactional state transitions, unique idempotency constraints, independent chain verification.
- **Reliability:** resumable background jobs; no blind retry after uncertain submission; durable audit evidence.
- **Performance:** local dashboard interaction under 500 ms for common reads on a small dataset; async processing for network-bound tasks.
- **Privacy:** minimize personal data; configurable retention; no personal data in transaction memo or public logs by default.
- **Observability:** structured logs, request/correlation IDs, metrics for submission, verification, failure, and unresolved payouts.
- **Maintainability:** migrations, typed schemas, documented interfaces, isolated settlement and agent adapters.
- **Portability:** Docker-based local environment and documented deployment assumptions.
- **Accessibility:** keyboard navigation, semantic labels, status not communicated by color alone.

## 9. Success measures

- 100% of executions have an approval matching the current batch hash.
- 0 known duplicate payouts from retried client commands.
- 100% of real `confirmed` payouts have independently verified network evidence.
- 100% of financial workflow commands emit audit events.
- Every unresolved payout is visible and assigned for reconciliation.
- Buildathon demo can show policy/eligibility → proposal → approval → receipt/evidence → audit.
- Agent tool calls are inspectable and evaluated, not merely presented as chat.

## 10. Release definition

A release is complete only when its milestone acceptance criteria, tests, docs, and threat-model checks pass. A running local simulation is not proof of a working Stellar testnet or Omega SDK integration.
