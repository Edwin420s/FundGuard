;; ============================================================================
;; Omega FundGuard — Cognitive Architecture: negotiation.metta
;; Multi-Party Governance, Separation of Duties & Quorum Consensus
;; ============================================================================

;; Separation of duties:
;; The proposer of a batch CANNOT be the approver of that batch
(= (is-separation-of-duties-satisfied $proposer $approver)
   (!= $proposer $approver))

;; Quorum consensus check:
;; For batches exceeding threshold (e.g., > 1,000 XLM / 10,000,000,000 stroops), dual approval required
(= (requires-dual-approval $totalStroops $thresholdStroops)
   (> $totalStroops $thresholdStroops))

;; Check if required approvals count is met
(= (is-quorum-reached $approvalsCount $requiredQuorum)
   (>= $approvalsCount $requiredQuorum))
