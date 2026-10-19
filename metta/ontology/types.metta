;; ============================================================================
;; Omega FundGuard — MeTTa Ontology Specification
;; Formal Typed Atomspace for Auditable AI Payout Operations
;; ============================================================================

(: Organization Type)
(: Competition Type)
(: Recipient Type)
(: FundingPolicy Type)
(: PayoutBatch Type)
(: Payout Type)
(: ApprovalRecord Type)
(: PaymentReceipt Type)
(: AuditHash Type)
(: StroopAmount Type)

;; Properties and Associations
(: has-organization (-> Competition Organization Atom))
(: has-policy (-> Competition FundingPolicy Atom))
(: target-eligible-count (-> FundingPolicy Number Atom))
(: minimum-eligible-count (-> FundingPolicy Number Atom))
(: total-fund-stroops (-> FundingPolicy StroopAmount Atom))

(: recipient-wallet (-> Recipient String Atom))
(: recipient-status (-> Recipient String Atom))
(: recipient-reliability-score (-> Recipient Number Atom))

(: batch-content-hash (-> PayoutBatch AuditHash Atom))
(: batch-approval-hash (-> PayoutBatch AuditHash Atom))
(: batch-status (-> PayoutBatch String Atom))
(: batch-total-stroops (-> PayoutBatch StroopAmount Atom))
(: batch-reserve-stroops (-> PayoutBatch StroopAmount Atom))

;; Status Constants
(: pending String)
(: verified String)
(: rejected String)
(: proposed String)
(: authorized String)
(: approved String)
(: simulated String)
(: confirmed String)
(: unresolved String)
(: failed String)

;; Unit Constants
(: STROOPS_PER_XLM Number)
(= (STROOPS_PER_XLM) 10000000)
