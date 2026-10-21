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

<!-- build trace 94 -->

<!-- build trace 95 -->

<!-- build trace 108 -->

<!-- build trace 109 -->

<!-- build trace 110 -->

<!-- build trace 111 -->

<!-- build trace 112 -->

<!-- build trace 113 -->

<!-- build trace 114 -->

<!-- build trace 115 -->

<!-- build trace 116 -->

<!-- build trace 118 -->

<!-- build trace 119 -->

<!-- build trace 120 -->

<!-- build trace 121 -->

<!-- build trace 122 -->

<!-- build trace 123 -->

<!-- build trace 124 -->

<!-- build trace 125 -->

<!-- build trace 127 -->

<!-- build trace 128 -->

<!-- build trace 129 -->

<!-- build trace 130 -->

<!-- build trace 131 -->

<!-- build trace 132 -->

<!-- build trace 133 -->

<!-- build trace 134 -->

<!-- build trace 135 -->

<!-- build trace 136 -->

<!-- build trace 137 -->

<!-- build trace 138 -->

<!-- build trace 139 -->

<!-- build trace 140 -->

<!-- build trace 141 -->

<!-- build trace 142 -->

<!-- build trace 143 -->

<!-- build trace 144 -->

<!-- build trace 145 -->

<!-- build trace 146 -->

<!-- build trace 147 -->

<!-- build trace 148 -->

<!-- build trace 149 -->

<!-- build trace 150 -->

<!-- build trace 151 -->

<!-- build trace 152 -->

<!-- build trace 153 -->

<!-- build trace 154 -->

<!-- build trace 155 -->

<!-- build trace 156 -->

<!-- build trace 157 -->

<!-- build trace 158 -->

<!-- build trace 159 -->

<!-- build trace 160 -->

<!-- build trace 162 -->

<!-- build trace 163 -->

<!-- build trace 164 -->

<!-- build trace 165 -->

<!-- build trace 166 -->

<!-- build trace 167 -->

<!-- build trace 168 -->

<!-- build trace 169 -->

<!-- build trace 170 -->

<!-- build trace 171 -->

<!-- build trace 172 -->

<!-- build trace 173 -->

<!-- build trace 174 -->

<!-- build trace 175 -->

<!-- build trace 176 -->

<!-- build trace 177 -->

<!-- build trace 178 -->

<!-- build trace 179 -->

<!-- build trace 180 -->

<!-- build trace 181 -->

<!-- build trace 182 -->

<!-- build trace 183 -->

<!-- build trace 184 -->

<!-- build trace 185 -->

<!-- build trace 186 -->

<!-- build trace 187 -->

<!-- build trace 188 -->

<!-- build trace 189 -->

<!-- build trace 190 -->

<!-- build trace 193 -->

<!-- build trace 194 -->

<!-- build trace 195 -->

<!-- build trace 196 -->

<!-- build trace 197 -->

<!-- build trace 198 -->

<!-- build trace 199 -->

<!-- build trace 200 -->

<!-- build trace 201 -->

<!-- build trace 202 -->

<!-- build trace 203 -->

<!-- build trace 204 -->

<!-- build trace 205 -->

<!-- build trace 206 -->

<!-- build trace 207 -->

<!-- build trace 208 -->

<!-- build trace 209 -->

<!-- build trace 210 -->

<!-- build trace 211 -->

<!-- build trace 212 -->

<!-- build trace 214 -->

<!-- build trace 215 -->

<!-- build trace 218 -->

<!-- build trace 219 -->

<!-- build trace 220 -->

<!-- build trace 221 -->

<!-- build trace 222 -->

<!-- build trace 223 -->

<!-- build trace 224 -->

<!-- build trace 225 -->

<!-- build trace 227 -->

<!-- build trace 228 -->
