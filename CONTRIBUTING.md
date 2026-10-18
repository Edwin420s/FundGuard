# Contributing

1. Read `docs/INDEX.md` and `docs/SECURITY.md`.
2. Work on a branch and make small, reviewable commits.
3. Add tests for state transitions, authorization, accounting, and error paths.
4. Never commit `.env`, private keys, real recipient PII, or production logs.
5. Do not mark integrations complete until their acceptance tests pass.
6. For payout logic, include an audit event and test idempotency/reconciliation.
7. Update docs and milestone status alongside code.
