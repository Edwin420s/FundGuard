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

<!-- build trace 229 -->

<!-- build trace 230 -->

<!-- build trace 231 -->

<!-- build trace 232 -->

<!-- build trace 233 -->

<!-- build trace 234 -->

<!-- build trace 235 -->

<!-- build trace 236 -->

<!-- build trace 237 -->

<!-- build trace 238 -->

<!-- build trace 240 -->

<!-- build trace 241 -->

<!-- build trace 242 -->

<!-- build trace 243 -->

<!-- build trace 244 -->

<!-- build trace 245 -->

<!-- build trace 246 -->

<!-- build trace 247 -->

<!-- build trace 248 -->

<!-- build trace 251 -->

<!-- build trace 252 -->

<!-- build trace 253 -->

<!-- build trace 254 -->

<!-- build trace 255 -->

<!-- build trace 256 -->

<!-- build trace 257 -->

<!-- build trace 258 -->

<!-- build trace 259 -->

<!-- build trace 260 -->

<!-- build trace 262 -->

<!-- build trace 263 -->

<!-- build trace 264 -->

<!-- build trace 265 -->

<!-- build trace 266 -->

<!-- build trace 267 -->

<!-- build trace 268 -->

<!-- build trace 269 -->

<!-- build trace 270 -->

<!-- build trace 271 -->

<!-- build trace 272 -->

<!-- build trace 273 -->

<!-- build trace 274 -->

<!-- build trace 275 -->

<!-- build trace 276 -->

<!-- build trace 277 -->

<!-- build trace 278 -->

<!-- build trace 279 -->

<!-- build trace 280 -->

<!-- build trace 281 -->

<!-- build trace 282 -->

<!-- build trace 283 -->

<!-- build trace 284 -->

<!-- build trace 285 -->

<!-- build trace 287 -->

<!-- build trace 288 -->

<!-- build trace 289 -->

<!-- build trace 290 -->

<!-- build trace 291 -->

<!-- build trace 292 -->

<!-- build trace 293 -->

<!-- build trace 294 -->

<!-- build trace 295 -->

<!-- build trace 297 -->

<!-- build trace 298 -->

<!-- build trace 299 -->

<!-- build trace 300 -->

<!-- build trace 301 -->

<!-- build trace 302 -->

<!-- build trace 303 -->

<!-- build trace 304 -->

<!-- build trace 305 -->

<!-- build trace 307 -->

<!-- build trace 309 -->

<!-- build trace 310 -->

<!-- build trace 311 -->

<!-- build trace 312 -->

<!-- build trace 313 -->

<!-- build trace 314 -->

<!-- build trace 315 -->

<!-- build trace 317 -->

<!-- build trace 318 -->

<!-- build trace 319 -->

<!-- build trace 320 -->

<!-- build trace 321 -->

<!-- build trace 323 -->

<!-- build trace 324 -->

<!-- build trace 325 -->

<!-- build trace 326 -->

<!-- build trace 327 -->

<!-- build trace 328 -->

<!-- build trace 329 -->

<!-- build trace 330 -->

<!-- build trace 331 -->

<!-- build trace 332 -->

<!-- build trace 333 -->

<!-- build trace 334 -->

<!-- build trace 335 -->

<!-- build trace 337 -->

<!-- build trace 338 -->

<!-- build trace 339 -->

<!-- build trace 340 -->

<!-- build trace 341 -->

<!-- build trace 342 -->

<!-- build trace 343 -->

<!-- build trace 344 -->

<!-- build trace 345 -->

<!-- build trace 349 -->

<!-- build trace 350 -->

<!-- build trace 351 -->

<!-- build trace 352 -->

<!-- build trace 353 -->

<!-- build trace 354 -->

<!-- build trace 355 -->

<!-- build trace 356 -->

<!-- build trace 357 -->

<!-- build trace 358 -->

<!-- build trace 359 -->

<!-- build trace 360 -->

<!-- build trace 361 -->

<!-- build trace 362 -->

<!-- build trace 363 -->

<!-- build trace 364 -->

<!-- build trace 365 -->

<!-- build trace 366 -->

<!-- build trace 367 -->

<!-- build trace 368 -->

<!-- build trace 369 -->

<!-- build trace 371 -->

<!-- build trace 372 -->

<!-- build trace 374 -->

<!-- build trace 375 -->

<!-- build trace 383 -->

<!-- build trace 384 -->

<!-- build trace 385 -->

<!-- build trace 386 -->

<!-- build trace 387 -->

<!-- build trace 388 -->

<!-- build trace 389 -->

<!-- build trace 391 -->

<!-- build trace 392 -->

<!-- build trace 393 -->

<!-- build trace 394 -->

<!-- build trace 396 -->

<!-- build trace 397 -->

<!-- build trace 399 -->

<!-- build trace 400 -->

<!-- build trace 401 -->

<!-- build trace 402 -->

<!-- build trace 403 -->

<!-- build trace 404 -->

<!-- build trace 405 -->

<!-- build trace 407 -->

<!-- build trace 408 -->

<!-- build trace 409 -->

<!-- build trace 410 -->

<!-- build trace 411 -->

<!-- build trace 412 -->

<!-- build trace 413 -->

<!-- build trace 414 -->

<!-- build trace 415 -->

<!-- build trace 416 -->

<!-- build trace 417 -->

<!-- build trace 418 -->

<!-- build trace 419 -->

<!-- build trace 420 -->

<!-- build trace 421 -->

<!-- build trace 422 -->

<!-- build trace 423 -->

<!-- build trace 424 -->

<!-- build trace 425 -->

<!-- build trace 426 -->

<!-- build trace 427 -->

<!-- build trace 428 -->

<!-- build trace 429 -->

<!-- build trace 430 -->

<!-- build trace 431 -->

<!-- build trace 432 -->

<!-- build trace 433 -->

<!-- build trace 434 -->

<!-- build trace 435 -->

<!-- build trace 436 -->

<!-- build trace 437 -->

<!-- build trace 438 -->

<!-- build trace 439 -->

<!-- build trace 441 -->
