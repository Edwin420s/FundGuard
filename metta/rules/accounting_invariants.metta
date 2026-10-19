;; ============================================================================
;; Omega FundGuard — MeTTa Accounting Invariants Rules
;; Conservation of Funds & Base-Unit Mathematical Guarantees
;; ============================================================================

;; Primary Accounting Invariant:
;; Total Fund = Released Allocation + Carry-Forward Reserve
(= (verify-accounting-invariant $totalFund $released $reserve)
   (== (+ $released $reserve) $totalFund))

;; Non-negativity invariant:
;; Balance must never be less than zero
(= (verify-non-negative-balance $balance)
   (>= $balance 0))

;; Fund solvency check:
;; Proposed obligations must never exceed available treasury balance
(= (verify-treasury-solvency $availableBalance $proposedObligation)
   (>= $availableBalance $proposedObligation))

;; Canonical Hash Verification:
;; Human approval must match the exact canonical SHA-256 batch hash
(= (verify-approval-binding $proposedHash $approvedHash)
   (== $proposedHash $approvedHash))
