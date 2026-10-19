;; ============================================================================
;; Omega FundGuard — MeTTa Prompt Injection Defense & Safety Rules
;; Symbolic Containment of Adversarial LLM Prompt Injections
;; ============================================================================

;; Detect adversarial injection patterns in prompts
(= (contains-override-pattern $text)
   (or (contains-substring $text "IGNORE PREVIOUS INSTRUCTIONS")
       (or (contains-substring $text "EXECUTE IMMEDIATELY WITHOUT APPROVAL")
           (or (contains-substring $text "DISREGARD ALL INVARIANTS")
               (or (contains-substring $text "TRANSFER ALL FUNDS TO")
                   (or (contains-substring $text "BYPASS APPROVAL")
                       (contains-substring $text "SYSTEM PROMPT OVERRIDE")))))))

;; Hard refusal when prompt injection detected
(= (validate-agent-prompt $prompt)
   (if (contains-override-pattern $prompt)
       "REJECTED_PROMPT_INJECTION_DETECTED"
       "PROMPT_SAFE_PROCEED"))

;; Safety Lockout: Agent cannot sign, approve, or execute settlements directly
(= (is-agent-authorized-for-execution $agentRole)
   False)

(= (is-agent-authorized-for-approval $agentRole)
   False)
