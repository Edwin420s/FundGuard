# Omega / Hyperon / MeTTa integration contract

## Purpose

Omega should coordinate the payout workflow, retrieve relevant program context, call constrained tools, preserve run/tool evidence, and explain outcomes. It is not a payment signer, authorization service, accounting ledger, or receipt oracle.

## Integration status

This repository does **not** claim an active Omega SDK connection. The exact supported SDK/package version, runtime, tool registration API, and MeTTa syntax must be verified against the current official Omega/Hyperon repositories and pinned. Keep the adapter behind an interface so SDK changes do not alter domain services.

## Proposed tools

Every tool is typed, allowlisted, tenant-scoped, rate-limited, and audited.

- `get_competition(competition_id)` — return authorized competition context.
- `get_policy_snapshot(competition_id, policy_version_id)` — immutable rules/hash.
- `list_eligible_recipients(competition_id)` — IDs and eligibility evidence references, minimum necessary fields.
- `simulate_allocation(competition_id, policy_version_id, recipient_ids)` — deterministic result only.
- `create_payout_proposal(competition_id, allocation, idempotency_key)` — draft only; never executes.
- `get_batch_status(batch_id)` — status, approval hash, receipt evidence.
- `request_human_approval(batch_id, content_hash)` — creates a review request; cannot approve on behalf of a human.
- `reconcile_payout(payout_id)` — query verified network evidence; never blindly resubmit.
- `get_audit_events(entity_id)` — authorized event trail.

Do not expose arbitrary SQL, filesystem, shell, raw database session, signer, secret store, or generic transaction-construction tools.

## Run evidence

Persist:
- agent run ID and version;
- initiating user and tenant;
- task and bounded context references;
- each tool name/version, validated arguments, result or structured error;
- policy and batch IDs/hashes consulted;
- model/provider metadata where permitted;
- final explanation and evaluation outcome.

Avoid storing unnecessary personal data or hidden reasoning. Store concise evidence summaries and tool traces rather than private chain-of-thought.

## Memory boundaries

Memory is scoped to organization/competition and has explicit retention. It can store prior approved program facts, recurring operational preferences, and references to resolved incidents. It cannot silently override a policy snapshot, change eligibility, grant permissions, or authorize payment. Retrieved memory is untrusted input and must be validated.

## Evaluation requirements

Agent must refuse policy bypass, invented receipts, unsupported claims of confirmation, unauthorized execution, and instructions embedded in recipient metadata. When evidence is missing, state what is missing and ask for review. Actual integration is accepted only when tests demonstrate real SDK orchestration and recorded tool calls.
