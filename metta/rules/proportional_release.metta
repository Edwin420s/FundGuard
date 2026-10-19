;; ============================================================================
;; Omega FundGuard — MeTTa Proportional Release & Financial Logic Rules
;; Track 02 — Omega payouts (Stellar testnet & Raven, Proportional release)
;; ============================================================================

;; Base-unit conversion rules
(= (xlm-to-stroops $xlm) (* $xlm 10000000))
(= (stroops-to-xlm $stroops) (/ $stroops 10000000))

;; Proportional release ratio calculation
;; Formula: min(1.0, eligible_count / target_eligible_count)
;; Minimum eligible count threshold must be met (e.g., at least 1)
(= (eligible-ratio $eligibleCount $targetCount)
   (if (<= $eligibleCount 0)
       0.0
       (if (>= $eligibleCount $targetCount)
           1.0
           (/ $eligibleCount $targetCount))))

;; Released allocation calculation in integer base units
(= (calculate-release $totalFundStroops $ratio)
   (* $totalFundStroops $ratio))

;; Carry-forward reserve calculation
;; All unreleased funds MUST carry forward into reserve
(= (calculate-reserve $totalFundStroops $releasedStroops)
   (- $totalFundStroops $releasedStroops))

;; Equal split allocation among verified winning recipients
(= (calculate-recipient-share $releasedStroops $eligibleCount)
   (if (<= $eligibleCount 0)
       0
       (/ $releasedStroops $eligibleCount)))

;; Illustrative fiat display conversion ($1 XLM = $0.10 USD illustration)
(= (illustrative-usd $stroops $priceCentsPerXlm)
   (/ (* (stroops-to-xlm $stroops) $priceCentsPerXlm) 100))
