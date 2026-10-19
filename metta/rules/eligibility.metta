;; ============================================================================
;; Omega FundGuard — MeTTa Recipient Eligibility Rules
;; Strict Evidence-Grounded Verification & Sybil Defense
;; ============================================================================

;; A recipient can only be paid if eligibility status is strictly "verified"
(= (is-recipient-eligible $status)
   (== $status "verified"))

;; Pending recipients must never receive allocated base units
(= (check-payout-eligibility $recipientId $status)
   (if (== $status "verified")
       "ELIGIBLE_FOR_ALLOCATION"
       "INELIGIBLE_PENDING_REVIEW"))

;; Self-asserted verification is prohibited: reviewers must be authorized
(= (validate-verification-reviewer $role)
   (if (or (== $role "organizer") (or (== $role "reviewer") (== $role "admin")))
       True
       False))

;; Address duplicate check across active competition recipients
(= (is-duplicate-wallet $walletA $walletB)
   (== $walletA $walletB))
