; Omega FundGuard - MeTTa Symbolic Policy & Reasoning Knowledge Base
; SingularityNET Omega / Hyperon / MeTTa Rule Declarations

; Types
(: FundingRule Type)
(: Policy Type)
(: Status Type)
(: Amount Type)
(: Invariant Type)

; Core Proportional Release Rule (Track 02 Specification)
; eligible-ratio = min(1.0, eligible / target)
(= (eligible-ratio $eligible $target)
   (if (>= $eligible $target)
       1.0
       (/ $eligible $target)))

; Released Fund = Total Fund * Release Ratio
(= (calculate-release $total $ratio)
   (* $total $ratio))

; Carry-Forward Reserve = Total Fund - Released Fund
(= (calculate-reserve $total $released)
   (- $total $released))

; Award per Recipient = Released / Count
(= (award-per-recipient $released $count)
   (if (== $count 0)
       0
       (/ $released $count)))

; Accounting Invariant Verification: Total == Allocated + Total Reserve
(= (verify-accounting-invariant $total $allocated $reserve)
   (== $total (+ $allocated $reserve)))

; Eligibility State Machine
(= (is-eligible-for-payout "verified") True)
(= (is-eligible-for-payout "pending") False)
(= (is-eligible-for-payout "rejected") False)
(= (is-eligible-for-payout "incomplete") False)

; Approval Hash Invariant
(= (is-approval-valid $approved-hash $current-hash)
   (== $approved-hash $current-hash))

; Safe Stop Rule on Missing Critical Evidence
(= (should-halt-on-missing-evidence $evidence-present)
   (if (== $evidence-present False)
       "HALT_AND_REQUEST_REVIEW"
       "PROCEED"))

; Prompt Injection Defense Guard
(= (sanitize-instruction $instruction)
   (if (== $instruction "ignore all rules")
       "POLICY_OVERRIDE_REJECTED"
       "INSTRUCTION_SAFE"))
