# Changelog — Omega FundGuard

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-24

### Added
- **Full Domain Model (15 Entities)**: Implemented complete relational domain model including `Organization`, `Membership`, `Competition`, `FundingPolicyVersion`, `Recipient`, `EligibilityDecision`, `PayoutBatch`, `Payout`, `Approval`, `SettlementAttempt`, `PaymentReceipt`, `ReconciliationCase`, `TreasuryReservation`, `AuditEvent`, `AgentRun`, and `AgentToolCall`.
- **Alembic Database Migrations**: Added full schema migration `f2c511826601_initial_full_schema.py` and closed-loop learning migration `bcaa6af974a2_add_learning_and_reliability_tables.py`.
- **MeTTa Symbolic Cognitive Architecture**:
  - `metta/ontology/types.metta`: Formal typed atomspace for competitions, policies, recipients, and hashes.
  - `metta/rules/proportional_release.metta`: Track 02 proportional release formula (e.g. 20 eligible / 50 target = 40% release), winner share allocation, and carry-forward reserves.
  - `metta/rules/eligibility.metta`: Recipient verification and duplicate wallet detection.
  - `metta/rules/accounting_invariants.metta`: Financial conservation laws ($\text{Total} = \text{Paid} + \text{Reserved} + \text{Available}$).
  - `metta/rules/prompt_injection_defense.metta`: Symbolic containment of adversarial prompt injections.
  - `metta/tests/test_rules.metta`: Self-contained MeTTa unit tests.
- **Omega Cognitive Subsystems**:
  - `omega/memory.metta`: Semantic, episodic, and belief state memory.
  - `omega/learning.metta`: Closed-loop learning from human adjudication, recipient reliability scoring ($0.0 \to 1.0$), and dynamic custom rule registration ("The Agent That Grows Up").
  - `omega/decisions.metta`: Safety policies, approval binding lockouts, and mainnet blocks.
  - `omega/skills.metta`: 11 allowlisted domain tool skill interfaces.
  - `omega/negotiation.metta`: Quorum consensus and separation-of-duties protocols.
- **Stellar SDK & Horizon Verification**:
  - Official Stellar SDK StrKey address validation (`StrKey.is_valid_ed25519_public_key`).
  - Independent Horizon transaction and payment-operation verification.
  - Support for `SimulatedSettlementAdapter` and `StellarTestnetAdapter`.
- **NEAR Intents Cross-Chain Simulator**:
  - Real-time dry quote simulator (`/api/v1/near-intents/quote`) with exchange rates, fees, and slippage.
- **Treasury Ledger & Reconciliation Cases**:
  - Strict integer base-unit accounting (stroops).
  - Unresolved payout case logging and operator resolution workflow.
- **Cryptographic Audit Trail**:
  - Per-competition SHA-256 hash chaining with integrity verification and JSON/CSV exports.
- **Full-Featured React Dashboard (11 Views)**:
  - Added Overview, Recipients, Policies, Batches, MeTTa Agent, Closed-Loop Learning, Treasury, NEAR Quotes, Reconciliation, Audit Trail, and Setup views.
- **Adversarial Benchmark Evaluation Suite**:
  - 5-benchmark adversarial evaluator testing prompt injection defense, ineligible refusal, unauthorized execution refusal, hallucinated receipt refusal, and MeTTa consistency.
- **Comprehensive Automated Test Suite**:
  - 18 backend pytest tests passing 100%.
  - Vitest frontend tests and Vite production build verified.

---

## [0.1.0] - 2026-10-23
### Initial Prototype Baseline
- Initial demo competition and recipient records.
- Basic simulated batch proposal and hash calculation.

<!-- build trace 55 -->

<!-- build trace 56 -->

<!-- build trace 57 -->

<!-- build trace 58 -->

<!-- build trace 59 -->

<!-- build trace 60 -->

<!-- build trace 61 -->

<!-- build trace 62 -->

<!-- build trace 66 -->

<!-- build trace 73 -->

<!-- build trace 84 -->

<!-- build trace 85 -->

<!-- build trace 86 -->

<!-- build trace 87 -->

<!-- build trace 88 -->

<!-- build trace 89 -->

<!-- build trace 90 -->

<!-- build trace 92 -->

<!-- build trace 93 -->
