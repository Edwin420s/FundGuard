;; ============================================================================
;; Omega FundGuard — MeTTa Rules Self-Verification Tests
;; ============================================================================

;; Test 1: XLM to stroops conversion
!(assertEqual (xlm-to-stroops 1700) 17000000000)

;; Test 2: Track 02 Proportional release: 20 eligible out of 50 target = 40%
!(assertEqual (eligible-ratio 20 50) 0.4)

;; Test 3: Total fund $1,700 (17,000,000,000 stroops) released at 40%
!(assertEqual (calculate-release 17000000000 0.4) 6800000000.0)

;; Test 4: Carry forward reserve calculation ($1,700 - $680 = $1,020)
!(assertEqual (calculate-reserve 17000000000 6800000000.0) 10200000000.0)

;; Test 5: Primary accounting invariant verification
!(assertEqual (verify-accounting-invariant 17000000000 6800000000.0 10200000000.0) True)

;; Test 6: Recipient share calculation (20 winners sharing $680 = $34/winner)
!(assertEqual (calculate-recipient-share 6800000000 20) 340000000.0)

;; Test 7: Recipient eligibility verification check
!(assertEqual (is-recipient-eligible "verified") True)
!(assertEqual (is-recipient-eligible "pending") False)

;; Test 8: Solvency check (Treasury has 10,200,000,000 stroops, request 6,800,000,000 stroops)
!(assertEqual (verify-treasury-solvency 10200000000 6800000000) True)

;; Test 9: Non-negative balance check
!(assertEqual (verify-non-negative-balance 0) True)
!(assertEqual (verify-non-negative-balance 10000000) True)

;; Test 10: Agent self-execution refusal invariant
!(assertEqual (is-agent-authorized-for-execution "omega_orchestrator") False)
