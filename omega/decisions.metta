;; ============================================================================
;; Omega FundGuard — Cognitive Architecture: decisions.metta
;; Safety Decision Policies, Lockout Protocols & Approval Binding
;; ============================================================================

;; Decision Policy 01: Human Approval Binding Lockout
;; A batch CANNOT execute unless the approved hash matches the proposal hash exactly
(= (is-batch-executable $batchStatus $approvalHash $contentHash)
   (if (and (== $batchStatus "approved") (== $approvalHash $contentHash))
       "EXECUTABLE"
       "LOCKOUT_UNAPPROVED_OR_HASH_MISMATCH"))

;; Decision Policy 02: Mainnet Safety Lockout
;; Live mainnet transfers remain strictly disabled
(= (is-network-permitted $network)
   (if (or (== $network "stellar-testnet") (== $network "simulated"))
       "PERMITTED"
       "LOCKOUT_MAINNET_DISABLED"))

;; Decision Policy 03: Idempotency Protection
;; Re-submission with the same idempotency key must return existing batch, not duplicate
(= (check-idempotency-collision $storedKey $incomingKey)
   (== $storedKey $incomingKey))

;; Decision Policy 04: Partial Settlement Action
;; If some payouts fail or timeout into unresolved, the batch enters partial state
(= (derive-batch-state $confirmedCount $unresolvedCount $failedCount $totalCount)
   (if (> $unresolvedCount 0)
       "unresolved"
       (if (and (> $confirmedCount 0) (< $confirmedCount $totalCount))
           "partially_confirmed"
           (if (== $confirmedCount $totalCount)
               "confirmed"
               "failed"))))
