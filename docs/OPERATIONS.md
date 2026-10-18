# Operations and deployment

## Local development

See README quick start. Default settlement mode is `simulated`.

## Environment configuration

- `DATABASE_URL`: SQLite for local run or PostgreSQL in Compose.
- `CORS_ORIGINS`: exact trusted browser origins.
- `SETTLEMENT_MODE`: currently `simulated`; unsupported real mode raises an error.
- `ALLOW_STELLAR_TESTNET`: must remain false until a reviewed adapter is implemented.
- `ALLOW_STELLAR_MAINNET`: must remain false for this project release.
- Stellar network passphrase and Horizon URL are configuration only; setting them does not activate settlement.

Do not store private keys/seeds in environment variables for production. Use a dedicated signer/custody integration with scoped policy.

## Database

Local startup calls SQLAlchemy `create_all` for convenience. Production must use Alembic migrations and a controlled release process. Back up the database and test restoration. Use least-privilege credentials and encrypt backups.

## Observability

Production logs should include request ID, correlation ID, tenant ID, batch/payout ID, adapter, attempt number, and outcome class. Never log signing secrets, access tokens, raw private identity evidence, or unnecessary personal data.

Metrics to add:
- API error rate and latency.
- batch proposals, approvals, executions, and failures.
- count/value of unresolved payouts and age of oldest case.
- settlement verification latency and mismatch count.
- queue lag and failed reconciliation jobs.
- agent tool-call failure and policy refusal rates.

## Recovery rules

- A timeout is not proof of failure.
- Search the network for the exact transaction/operation before retry.
- Keep unresolved amount reserved.
- Record operator, evidence, decision, and reason for every manual resolution.
- Never change a confirmed receipt to failed without a compensating/reversal process and explicit evidence.

## Incident response

1. Pause new execution.
2. Revoke compromised user/API credentials and signer authorization.
3. Preserve logs, batch hashes, approvals, network transaction evidence, and relevant timestamps.
4. Reconcile every submitted/unresolved payout.
5. Notify accountable organization owners and follow legal/contractual duties.
6. Document root cause and preventive actions before resuming.

## Deployment hardening checklist

- [ ] TLS and secure headers.
- [ ] AuthN, RBAC, tenant isolation, rate limits.
- [ ] Secret manager and signer separation.
- [ ] Migrations, backups, restore test.
- [ ] Monitoring, alerts, incident contact.
- [ ] Dependency and container scan.
- [ ] Privacy/retention/legal review.
- [ ] Testnet smoke test; mainnet remains disabled.
