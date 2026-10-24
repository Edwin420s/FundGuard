import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react'
import App from './App.jsx'

describe('FundGuard End-to-End Frontend User Journey', () => {
  let mockState = {}

  beforeEach(() => {
    window.scrollTo = vi.fn()
    localStorage.clear()

    // Initialize mock database state for this end-to-end run
    mockState = {
      user: null,
      competitions: [],
      policies: [],
      recipients: [],
      batches: [],
      audit: [],
      reconciliationCases: [],
      treasury: {
        competition_id: 'comp-acme-1',
        currency: 'XLM',
        total_fund_base_units: 25000000000,
        paid_base_units: 0,
        reserved_base_units: 0,
        proposed_base_units: 0,
        available_base_units: 25000000000,
        carry_forward_reserve_base_units: 0
      }
    }

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url, options = {}) => {
      const method = options.method || 'GET'
      const body = options.body ? JSON.parse(options.body) : null

      // Auth Registration
      if (url.includes('/auth/register') && method === 'POST') {
        const userObj = {
          id: 'user-alice-01',
          email: body.email,
          full_name: body.full_name,
          organization_id: 'org-acme-01',
          organization_name: body.organization_name,
          role: 'sponsor'
        }
        const compObj = {
          id: 'comp-acme-1',
          name: `${body.organization_name} Primary Fund`,
          description: `Primary disbursement workspace for ${body.organization_name}`,
          organization_id: 'org-acme-01',
          network: 'stellar-testnet'
        }
        const policyObj = {
          id: 'pol-acme-1',
          competition_id: compObj.id,
          version: 1,
          status: 'active',
          rules_hash: '9a3f2b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a',
          rules: {
            total_fund: { amount_base_units: 25000000000, currency: 'XLM' },
            release_rule: { type: 'proportional', target_eligible_count: 10, minimum_eligible_count: 1 }
          },
          created_at: new Date().toISOString()
        }

        mockState.user = userObj
        mockState.competitions = [compObj]
        mockState.policies = [policyObj]
        mockState.audit.push({
          id: 'evt-1',
          action: 'user.registered',
          actor: body.full_name,
          entity_type: 'user',
          entity_id: userObj.id,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })

        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            user: userObj,
            default_competition_id: compObj.id,
            token: 'jwt-acme-token-alice'
          })
        })
      }

      // Custody Account
      if (url.includes('/stellar/custody')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            account_id: 'GACMEPAYOUTVAULT1234567890ABCDEF1234567890ABCDEF12345678',
            xlm_balance: '10000.0000000',
            balances: [{ asset_type: 'native', balance: '10000.0000000' }],
            subentry_count: 0,
            sequence: 101,
            network: 'stellar-testnet',
            horizon_url: 'https://horizon-testnet.stellar.org',
            funded: true
          })
        })
      }

      // Competitions List
      if (url.includes('/competitions') && !url.includes('/policies') && !url.includes('/recipients') && !url.includes('/batches')) {
        if (method === 'POST') {
          const newComp = {
            id: `comp-acme-${mockState.competitions.length + 1}`,
            name: body.name,
            description: body.description,
            organization_id: body.organization_id || 'org-acme-01',
            network: 'stellar-testnet'
          }
          mockState.competitions.push(newComp)
          return Promise.resolve({ ok: true, json: () => Promise.resolve(newComp) })
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(mockState.competitions))) })
      }

      // Treasury Summary
      if (url.includes('/treasury/')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(mockState.treasury))) })
      }

      // Policies & Simulation
      if (url.includes('/policies/simulate')) {
        const ratio = Math.min(1.0, body.eligible_count / body.target_eligible_count)
        const released = Math.floor(body.total_fund_base_units * ratio)
        const reserve = body.total_fund_base_units - released
        const perWinner = body.eligible_count > 0 ? Math.floor(released / body.eligible_count) : 0
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            simulation_parameters: body,
            calculated_outcome: {
              eligible_count: body.eligible_count,
              target_eligible_count: body.target_eligible_count,
              release_ratio: ratio,
              released_base_units: released,
              total_reserve_base_units: reserve,
              amount_per_recipient_base_units: perWinner
            }
          })
        })
      }

      if (url.includes('/policies') && method === 'POST') {
        const newVer = mockState.policies.length + 1
        const pol = {
          id: `pol-acme-${newVer}`,
          competition_id: 'comp-acme-1',
          version: newVer,
          status: 'active',
          rules_hash: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
          rules: {
            total_fund: { amount_base_units: body.total_fund_base_units, currency: body.currency },
            release_rule: { type: 'proportional', target_eligible_count: body.target_eligible_count, minimum_eligible_count: 1 }
          },
          created_at: new Date().toISOString()
        }
        mockState.policies.forEach(p => { p.status = 'superseded' })
        mockState.policies.unshift(pol)
        mockState.audit.push({
          id: `evt-${mockState.audit.length + 1}`,
          action: 'policy.created',
          actor: 'Alice Director',
          entity_type: 'funding_policy_version',
          entity_id: pol.id,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })
        return Promise.resolve({ ok: true, json: () => Promise.resolve(pol) })
      }

      if (url.includes('/policies')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(mockState.policies))) })
      }

      // Recipients
      if (url.includes('/recipients/bulk') && method === 'POST') {
        const created = body.recipients.map((r, idx) => ({
          id: `rec-bulk-${idx + 1}`,
          competition_id: 'comp-acme-1',
          display_name: r.display_name,
          wallet_address: r.wallet_address,
          eligibility_status: body.auto_verify ? 'verified' : 'pending',
          eligibility_note: r.eligibility_note,
          is_valid_strkey: true,
          created_at: new Date().toISOString()
        }))
        mockState.recipients.push(...created)
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            imported_count: created.length,
            verified_count: body.auto_verify ? created.length : 0,
            failed_count: 0
          })
        })
      }

      if (url.includes('/recipients') && url.includes('/verify') && method === 'POST') {
        const recId = url.split('/recipients/')[1].split('/verify')[0]
        const rec = mockState.recipients.find(r => r.id === recId)
        if (rec) rec.eligibility_status = 'verified'
        mockState.audit.push({
          id: `evt-${mockState.audit.length + 1}`,
          action: 'recipient.verified',
          actor: 'Alice Director',
          entity_type: 'recipient',
          entity_id: recId,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })
        return Promise.resolve({ ok: true, json: () => Promise.resolve(rec) })
      }

      if (url.includes('/recipients') && method === 'POST') {
        const newRec = {
          id: `rec-single-${mockState.recipients.length + 1}`,
          competition_id: 'comp-acme-1',
          display_name: body.display_name,
          wallet_address: body.wallet_address,
          eligibility_status: body.eligibility_status || 'pending',
          eligibility_note: body.eligibility_note || '',
          is_valid_strkey: true,
          created_at: new Date().toISOString()
        }
        mockState.recipients.push(newRec)
        mockState.audit.push({
          id: `evt-${mockState.audit.length + 1}`,
          action: 'recipient.created',
          actor: body.created_by || 'Alice Director',
          entity_type: 'recipient',
          entity_id: newRec.id,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })
        return Promise.resolve({ ok: true, json: () => Promise.resolve(newRec) })
      }

      if (url.includes('/recipients')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(mockState.recipients))) })
      }

      // AI Proposal Agent
      if (url.includes('/agent/run') && method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            intent: 'generate_payout_proposal',
            status: 'completed',
            summary: 'Evaluated verified recipients against proportional policy. Recommends distributing 500.00 XLM per verified team with 1,500.00 XLM carry-forward reserve.',
            structured_output: {
              batch_name: 'Acme Innovation Award Batch 1',
              amount_per_recipient_xlm: 500,
              reserve_xlm: 1500,
              payouts: mockState.recipients.filter(r => r.eligibility_status === 'verified').map(r => ({
                recipient_id: r.id,
                display_name: r.display_name,
                wallet_address: r.wallet_address,
                amount_base_units: 5000000000
              }))
            }
          })
        })
      }

      // Batches & Workflows
      if (url.includes('/batches') && !url.includes('/approve') && !url.includes('/execute') && !url.includes('/settle') && !url.includes('/cancel') && method === 'POST') {
        const recipientIds = body.recipient_ids || (mockState.recipients.filter(r => r.eligibility_status === 'verified').map(r => r.id))
        const amountPer = body.amount_base_units || 5000000000
        const totalBase = amountPer * (recipientIds.length || 1)
        const reserveBase = body.reserve_base_units !== undefined ? body.reserve_base_units : 15000000000
        const newBatch = {
          id: 'batch-acme-101',
          competition_id: 'comp-acme-1',
          batch_name: body.batch_name || 'Acme Innovation Batch 1',
          status: 'proposed',
          content_hash: 'c8f7d6e5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7',
          policy_version_id: 'pol-acme-1',
          total_base_units: String(totalBase),
          reserve_base_units: String(reserveBase),
          created_by: body.created_by || 'Alice Director',
          created_at: new Date().toISOString(),
          payouts: recipientIds.map((recId, idx) => ({
            id: `pay-${idx + 1}`,
            recipient_id: recId,
            display_name: mockState.recipients.find(r => r.id === recId)?.display_name || 'Delta Quantum Labs',
            wallet_address: mockState.recipients.find(r => r.id === recId)?.wallet_address || 'GA7SFOTHBSSRUGL4NUYZXCQTO2MDDJYUIEVPYIYPCYD2BR2RQOVNXIHD',
            amount_base_units: String(amountPer),
            status: 'proposed'
          }))
        }
        mockState.batches.unshift(newBatch)
        mockState.treasury.proposed_base_units = totalBase
        mockState.audit.push({
          id: `evt-${mockState.audit.length + 1}`,
          action: 'batch.proposed',
          actor: 'Alice Director',
          entity_type: 'payout_batch',
          entity_id: newBatch.id,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })
        return Promise.resolve({ ok: true, json: () => Promise.resolve(newBatch) })
      }

      if (url.includes('/batches') && url.includes('/approve') && method === 'POST') {
        const batch = mockState.batches[0]
        batch.status = 'approved'
        batch.approved_by = 'Finance Director'
        batch.approved_at = new Date().toISOString()
        mockState.treasury.reserved_base_units = Number(batch.total_base_units)
        mockState.treasury.proposed_base_units = 0
        mockState.audit.push({
          id: `evt-${mockState.audit.length + 1}`,
          action: 'batch.approved',
          actor: 'Finance Director',
          entity_type: 'payout_batch',
          entity_id: batch.id,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })
        return Promise.resolve({ ok: true, json: () => Promise.resolve(batch) })
      }

      if (url.includes('/batches') && (url.includes('/settle') || url.includes('/execute')) && method === 'POST') {
        const batch = mockState.batches[0]
        batch.status = 'confirmed'
        batch.payouts.forEach(p => {
          p.status = 'confirmed'
          p.stellar_tx_hash = '5d4f3e2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e'
        })
        mockState.treasury.paid_base_units = Number(batch.total_base_units)
        mockState.treasury.reserved_base_units = 0
        mockState.treasury.available_base_units = mockState.treasury.total_fund_base_units - Number(batch.total_base_units)
        mockState.treasury.carry_forward_reserve_base_units = Number(batch.reserve_base_units)
        mockState.audit.push({
          id: `evt-${mockState.audit.length + 1}`,
          action: 'batch.settled',
          actor: 'Alice Director',
          entity_type: 'payout_batch',
          entity_id: batch.id,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })
        return Promise.resolve({ ok: true, json: () => Promise.resolve(batch) })
      }

      if (url.includes('/batches')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(mockState.batches))) })
      }

      // Reconciliation
      if (url.includes('/reconciliation/cases') && method === 'POST') {
        const caseId = url.split('/cases/')[1].split('/resolve')[0]
        const rc = mockState.reconciliationCases.find(c => c.id === caseId)
        if (rc) {
          rc.status = `resolved_${body.decision}`
          rc.resolved_by = body.reviewer
          rc.resolution_note = body.resolution_note
        }
        mockState.audit.push({
          id: `evt-${mockState.audit.length + 1}`,
          action: `reconciliation.${body.decision}`,
          actor: body.reviewer,
          entity_type: 'reconciliation_case',
          entity_id: caseId,
          integrity_valid: true,
          created_at: new Date().toISOString()
        })
        return Promise.resolve({ ok: true, json: () => Promise.resolve(rc) })
      }

      if (url.includes('/reconciliation/cases')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(mockState.reconciliationCases))) })
      }

      // Audit Trail
      if (url.includes('/audit/events')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(JSON.stringify(mockState.audit))) })
      }

      // NEAR Intents Quote
      if (url.includes('/near-intents/quote')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            source_amount_display: '1.00 XLM',
            estimated_destination_amount: '0.0850 NEAR',
            simulated_exchange_rate: '0.085',
            slippage_tolerance_pct: '0.5%',
            estimated_network_fee_stroops: '100'
          })
        })
      }

      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))
  })

  afterEach(() => {
    cleanup()
    localStorage.clear()
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('completes the entire user lifecycle from landing to settlement, treasury verification, and signout', async () => {
    // 1. Landing Page Navigation
    render(<App initialView="landing" />)
    expect(screen.getByText(/Automated, Verifiable Program Disbursements/i)).toBeTruthy()

    // Click Create Account from hero section
    const createAcctBtn = screen.getAllByRole('button', { name: /Create Free Account/i })[0]
    fireEvent.click(createAcctBtn)

    // 2. Signup & Account Registration
    expect(screen.getByRole('heading', { name: /Create Your Account/i })).toBeTruthy()
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Alex Morgan/i), { target: { value: 'Alice Director' } })
    fireEvent.change(screen.getByPlaceholderText(/alex@organization\.com/i), { target: { value: 'alice@acmefoundation.org' } })
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Apex Global Foundation/i), { target: { value: 'Acme Foundation' } })
    fireEvent.change(screen.getByPlaceholderText(/Choose a secure password/i), { target: { value: 'SecurePass2026!' } })

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))

    // 3. User Dashboard & Isolation Verification
    await waitFor(() => {
      expect(screen.getByText('Alice Director')).toBeTruthy()
      expect(screen.getAllByText(/Acme Foundation/i).length).toBeGreaterThan(0)
    })
    expect(screen.getAllByText('Acme Foundation Primary Fund').length).toBeGreaterThan(0)

    // 4. Add Recipient & Verification
    const recipientsTabBtn = screen.getByRole('button', { name: /Recipients & Teams/i })
    fireEvent.click(recipientsTabBtn)
    expect(screen.getByRole('heading', { name: /Add Recipient Team/i })).toBeTruthy()

    // Add Single Recipient
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Team Northstar/i), { target: { value: 'Delta Quantum Labs' } })
    fireEvent.change(screen.getByPlaceholderText(/G\.\.\./i), {
      target: { value: 'GA7SFOTHBSSRUGL4NUYZXCQTO2MDDJYUIEVPYIYPCYD2BR2RQOVNXIHD' }
    })
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Verified eligibility criteria met/i), {
      target: { value: 'Innovation Track 1 Winner' }
    })
    fireEvent.click(screen.getByRole('button', { name: /Register Recipient/i }))

    await waitFor(() => {
      expect(screen.getByText('Delta Quantum Labs')).toBeTruthy()
      expect(screen.getByText('pending')).toBeTruthy()
    })

    // Verify Recipient
    const verifyBtn = screen.getByRole('button', { name: /Verify Eligibility/i })
    fireEvent.click(verifyBtn)

    await waitFor(() => {
      expect(screen.getByText('verified')).toBeTruthy()
    })

    // 5. Bulk CSV Upload
    const uploadCsvTabBtn = screen.getByRole('button', { name: /Upload CSV File/i })
    fireEvent.click(uploadCsvTabBtn)
    expect(screen.getByText(/Bulk Import Recipients via CSV/i)).toBeTruthy()

    // 6. Award Rules & Calculator Simulation and Committing New Policy Version
    const policyTabBtn = screen.getByRole('button', { name: /Award Rules & Calculator/i })
    fireEvent.click(policyTabBtn)

    expect(screen.getByRole('heading', { name: /Proportional Award Calculator/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /Commit New Policy Version/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /Policy Version History/i })).toBeTruthy()

    // Commit a new policy version (v2)
    const commitPolicyBtn = screen.getByRole('button', { name: /Commit Policy Version/i })
    fireEvent.click(commitPolicyBtn)

    await waitFor(() => {
      expect(screen.getByText(/Funding policy version v2 committed/i)).toBeTruthy()
    })

    // 7. Payout Batches & AI Proposal
    const batchesTabBtn = screen.getByRole('button', { name: /Payout Batches/i })
    fireEvent.click(batchesTabBtn)
    expect(screen.getByRole('heading', { name: /Draft Payout Batch/i })).toBeTruthy()

    // Trigger AI Auto-Draft Proposal
    const aiDraftBtn = screen.getByRole('button', { name: /Auto-Draft Proposal \(AI\)/i })
    await waitFor(() => {
      expect(aiDraftBtn.disabled).toBe(false)
    })
    fireEvent.click(aiDraftBtn)

    await waitFor(() => {
      expect(screen.getByText(/AI Auto-Draft completed/i)).toBeTruthy()
    })

    // 8. Dual-Signoff Reviewer Approval
    const approveBtn = screen.getByRole('button', { name: /Authorize Only \(Hold\)/i })
    expect(approveBtn).toBeTruthy()
    fireEvent.click(approveBtn)

    await waitFor(() => {
      expect(screen.getAllByText(/APPROVED/i).length).toBeGreaterThan(0)
    })

    // 9. Batch Settlement Execution
    const settleBtn = screen.getByRole('button', { name: /Execute Settlement/i })
    expect(settleBtn).toBeTruthy()
    fireEvent.click(settleBtn)

    await waitFor(() => {
      expect(screen.getAllByText(/\[Settled\]/i).length).toBeGreaterThan(0)
    })

    // 10. Treasury & Invariants Solvency Verification
    const treasuryTabBtn = screen.getByRole('button', { name: /Treasury & Audit Trail/i })
    fireEvent.click(treasuryTabBtn)

    expect(screen.getByRole('heading', { name: /Treasury Ledger Breakdown/i })).toBeTruthy()
    expect(screen.getByText(/\[Solvency Verified\] Paid \+ Reserve equals 100% of the initial prize pool\./i)).toBeTruthy()

    // Check Reconciliation Section
    expect(screen.getByRole('heading', { name: /Disbursement Reconciliation & Anomaly Management/i })).toBeTruthy()
    expect(screen.getByText(/0 Anomaly Cases Detected/i)).toBeTruthy()
    expect(screen.getByText('Clean Ledger')).toBeTruthy()

    // 11. Cryptographic Hash-Chained Audit Trail Verification
    expect(screen.getByRole('heading', { name: /Cryptographic Audit Trail/i })).toBeTruthy()
    expect(screen.getAllByText('Valid Hash').length).toBeGreaterThan(0)
    expect(screen.getByText(/batch\.settled/i)).toBeTruthy()

    // 12. Multi-Workspace Switch & Workspace Creation
    const workspacesTabBtn = screen.getByRole('button', { name: /^Workspaces$/i })
    fireEvent.click(workspacesTabBtn)

    expect(screen.getByRole('heading', { name: /Create New Workspace/i })).toBeTruthy()
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. AI Agents Ecosystem Grants/i), { target: { value: 'Acme Innovation Grants 2026' } })
    fireEvent.click(screen.getByRole('button', { name: /Create Workspace/i }))

    await waitFor(() => {
      expect(screen.getByText(/Workspace "Acme Innovation Grants 2026" created/i)).toBeTruthy()
    })

    // 13. Log Out and Return to Public Landing Page
    const logoutBtn = screen.getByRole('button', { name: /Log Out/i })
    fireEvent.click(logoutBtn)

    await waitFor(() => {
      expect(screen.getByText(/Automated, Verifiable Program Disbursements/i)).toBeTruthy()
      expect(screen.queryByText('Alice Director')).toBeNull()
    })
  })
})
