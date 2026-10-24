# Executive Product Walkthrough Script

## Before recording
- Start API and frontend.
- Open the dashboard and `/docs`.
- Use only synthetic recipient names and test-looking public addresses.
- Keep the settlement mode set to `simulated`.
- Do not imply a simulated receipt exists on Stellar.

## 0:00–0:25 — Problem
“Prize payout workflows are spread across spreadsheets and chat. FundGuard makes each award traceable from eligibility and allocation through human approval and settlement evidence.”

## 0:25–0:50 — Create workspace and recipient
Create a competition. Register a recipient. Show that the recipient starts `pending`; use the demo reviewer action to verify eligibility.

## 0:50–1:20 — Create proposal
Select the eligible recipient, enter an integer amount in stroops, and generate a batch. Point out the canonical SHA-256 content hash and the payout total.

## 1:20–1:45 — Human approval
Approve the exact content hash. Explain that an altered proposal cannot reuse this approval.

## 1:45–2:10 — Safe execution
Run the simulation. State explicitly: “This local receipt is simulated and no Stellar transaction has been sent. The real adapter must independently verify network evidence before a payout can be called confirmed.”

## 2:10–2:40 — Audit
Open audit trail and verify hash chain. Show proposal, approval, and simulated execution events.

## 2:40–3:00 — Omega architecture
Explain Omega is intended to retrieve policy context and call typed tools; deterministic code enforces money and approval rules. Show the agent integration plan and disclose that actual SDK wiring is still a separate integration milestone unless it has been completed and tested by the team.
