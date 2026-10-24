# Documentation index

Read in this order:

1. [`PRD.md`](PRD.md) — problem, users, capabilities, product requirements, and success measures.
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — services, trust boundaries, data flow, and integration boundaries.
3. [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) — entities, invariants, constraints, and state transitions.
4. [`API_REFERENCE.md`](API_REFERENCE.md) — current API routes, examples, and expected errors.
5. [`IMPLEMENTATION_MILESTONES.md`](IMPLEMENTATION_MILESTONES.md) — complete delivery plan and testable acceptance criteria.
6. [`SECURITY.md`](SECURITY.md) — threat model, security controls, and production release gates.
7. [`TEST_PLAN.md`](TEST_PLAN.md) — unit, integration, adversarial, and network tests.
8. [`OPERATIONS.md`](OPERATIONS.md) — local run, deployment, backups, monitoring, recovery, and incident handling.
9. [`OMEGA_AGENT.md`](OMEGA_AGENT.md) — agent responsibilities, tool contract, memory boundaries, and evaluation.
10. [`STELLAR_INTEGRATION.md`](STELLAR_INTEGRATION.md) — safe integration requirements for testnet and evidence verification.
11. [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) — an executive product demonstration walkthrough.
12. [`DECISIONS.md`](DECISIONS.md) — architectural decisions and rationale.

## Status convention

- **Implemented:** present in code and runnable locally.
- **Designed:** specified but not fully implemented.
- **Integration required:** external SDK, credentials, infrastructure, or independent verification is still required.
- **Production gate:** must be satisfied before any live-money use.

Do not infer implementation from a planned milestone. The README and this status convention distinguish working local demo features from integrations that still require completion.
