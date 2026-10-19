;; ============================================================================
;; Omega FundGuard — Cognitive Architecture: learning.metta
;; Closed-Loop Learning, Recipient Reliability Scoring & Dynamic Rule Evolution
;; "The Agent That Grows Up"
;; ============================================================================

;; Record human reviewer adjudication and update episodic memory
(= (record-human-adjudication $caseId $entityId $action $reviewer $reason)
   (assert-atom &self (human-adjudication $caseId $entityId $action $reviewer $reason)))

;; Recipient Reliability Scoring:
;; Initial default score: 1.0 (clean slate)
;; Promoted on verified successful settlement: min(1.0, current + 0.05)
;; Penalized on disputed/unresolved case: max(0.0, current - 0.25)
(= (calculate-updated-reliability $currentScore $eventOutcome)
   (if (== $eventOutcome "confirmed_settlement")
       (if (> (+ $currentScore 0.05) 1.0) 1.0 (+ $currentScore 0.05))
       (if (== $eventOutcome "dispute_penalty")
           (if (< (- $currentScore 0.25) 0.0) 0.0 (- $currentScore 0.25))
           $currentScore)))

;; Dynamic Rule Addition ("The Agent That Grows Up")
;; Human finance supervisors can register custom declarative MeTTa rewrite rules
;; that take effect immediately for future allocations and invariant checks.
(= (register-custom-learned-rule $ruleName $ruleExpression)
   (assert-atom &self (learned-rule $ruleName $ruleExpression)))

;; Query whether a recipient meets dynamic trust threshold (e.g. reliability >= 0.70)
(= (is-trusted-recipient $reliabilityScore)
   (>= $reliabilityScore 0.70))

;; Adaptive allocation multiplier based on learned reliability score
(= (apply-reliability-multiplier $baseAmount $reliabilityScore)
   (if (>= $reliabilityScore 0.90)
       $baseAmount
       (* $baseAmount $reliabilityScore)))
