# Architecture decision records

## ADR-001 — Domain logic is deterministic
**Decision:** LLM/agent output cannot directly control monetary arithmetic, approval, or confirmation.  
**Reason:** language models can hallucinate and are not a financial system of record.

## ADR-002 — Simulation is the default
**Decision:** local demo uses a simulation adapter; real settlement is not enabled by a configuration flip alone.  
**Reason:** prevents a demo from accidentally transferring assets or misrepresenting synthetic evidence.

## ADR-003 — Integer base units
**Decision:** blockchain amounts use integer base units.  
**Reason:** avoids floating-point rounding errors and ambiguous asset precision.

## ADR-004 — Approval binds to canonical content hash
**Decision:** an approver authorizes a specific immutable proposal hash.  
**Reason:** any change to destination, amount, asset, reserve, or policy should require fresh approval.

## ADR-005 — Unresolved is a first-class state
**Decision:** ambiguous network outcomes are reconciled before retry.  
**Reason:** network timeouts can occur after successful submission, and blind retries risk duplicate payout.

## ADR-006 — Agent adapter is versioned
**Decision:** Omega SDK calls live behind an adapter with typed tool contracts.  
**Reason:** SDK APIs evolve and must be pinned/verified rather than guessed.

## ADR-007 — Testnet first, mainnet disabled
**Decision:** buildathon uses testnet design and simulation; mainnet remains disabled.  
**Reason:** financial, security, legal, and operational gates must be met before live money.
