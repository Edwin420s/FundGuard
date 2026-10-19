;; ============================================================================
;; Omega FundGuard — Cognitive Architecture: skills.metta
;; Registered Callable Skill Interfaces for Omega AI Agent
;; ============================================================================

(: Skill Type)

(: GetFundingPolicy Skill)
(: GetEligibleTeams Skill)
(: CalculateAllocation Skill)
(: ValidatePayoutBatch Skill)
(: RequestHumanApproval Skill)
(: GetApprovalStatus Skill)
(: ExecuteApprovedPayout Skill)
(: VerifyTransaction Skill)
(: ReconcilePayout Skill)
(: GetAuditHistory Skill)
(: GetSimulatedNearQuote Skill)

;; Skill Execution Guard:
;; The agent may only invoke allowlisted skills; arbitrary system command execution is rejected
(= (is-skill-allowlisted $skillName)
   (or (== $skillName "get_funding_policy")
   (or (== $skillName "get_eligible_teams")
   (or (== $skillName "calculate_allocation")
   (or (== $skillName "validate_payout_batch")
   (or (== $skillName "request_human_approval")
   (or (== $skillName "get_approval_status")
   (or (== $skillName "execute_approved_payout")
   (or (== $skillName "verify_transaction")
   (or (== $skillName "reconcile_payout")
   (or (== $skillName "get_audit_history")
       (== $skillName "get_simulated_near_quote"))))))))))))
