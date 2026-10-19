;; ============================================================================
;; Omega FundGuard — Cognitive Architecture: memory.metta
;; Semantic, Episodic, and Belief State Memory in MeTTa Atomspace
;; ============================================================================

;; --- 1. Semantic Memory ---
;; Invariant financial and cryptographic constants
(: ATOMSPACE_RESERVE_MODE String)
(= (ATOMSPACE_RESERVE_MODE) "carry_forward")

(: MAX_SINGLE_RECIPIENT_CAP StroopAmount)
(= (MAX_SINGLE_RECIPIENT_CAP) 10000000000) ;; 1,000 XLM cap per recipient

(: SETTLEMENT_TIMEOUT_SECONDS Number)
(= (SETTLEMENT_TIMEOUT_SECONDS) 60)

;; --- 2. Episodic Memory ---
;; Records historical occurrences: proposals, approvals, settlement outcomes
(= (record-episodic-proposal $batchId $contentHash $totalStroops $reserveStroops)
   (assert-atom &self (historical-proposal $batchId $contentHash $totalStroops $reserveStroops)))

(= (record-episodic-approval $batchId $approver $decision $approvedHash)
   (assert-atom &self (historical-approval $batchId $approver $decision $approvedHash)))

(= (record-episodic-settlement $payoutId $txHash $status $verifiedAt)
   (assert-atom &self (historical-settlement $payoutId $txHash $status $verifiedAt)))

;; --- 3. Belief State Register ---
;; Current working positions of the Treasury and Batch Orchestration
(= (update-treasury-belief $competitionId $paid $reserved $available)
   (assert-atom &self (treasury-state $competitionId $paid $reserved $available)))

(= (get-working-reserve $competitionId)
   (match &self (treasury-state $competitionId $paid $reserved $available) $reserved))
