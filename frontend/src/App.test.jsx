import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import App from './App.jsx'

describe('FundGuard Dashboard UI', () => {
  beforeEach(() => {
    window.scrollTo = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url) => {
      if (url.includes('/competitions') && !url.includes('/policies') && !url.includes('/recipients') && !url.includes('/batches')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: 'comp-101',
              name: 'FundGuard Test Challenge',
              description: 'Transparent Stellar payouts',
              network: 'stellar-testnet'
            }
          ])
        })
      }
      if (url.includes('/stellar/custody')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            account_id: 'GBZXN7PIRZGNMHGA728R420SFUNDGUARDDEMO1234567890ABCDEF12345678',
            xlm_balance: '10000.0000000',
            balances: [{ asset_type: 'native', balance: '10000.0000000' }],
            subentry_count: 0,
            sequence: 12345,
            network: 'stellar-testnet',
            horizon_url: 'https://horizon-testnet.stellar.org',
            funded: true
          })
        })
      }
      if (url.includes('/treasury')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            competition_id: 'comp-101',
            currency: 'XLM',
            total_fund_base_units: 17000000000,
            total_fund_display: '1700.00 XLM',
            paid_base_units: 6800000000,
            paid_display: '680.00 XLM',
            reserved_base_units: 0,
            reserved_display: '0.00 XLM',
            available_base_units: 10200000000,
            available_display: '1020.00 XLM',
            carry_forward_reserve_base_units: 10200000000,
            carry_forward_display: '1020.00 XLM'
          })
        })
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    }))
  })

  afterEach(() => {
    cleanup()
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('renders the product header and branding', () => {
    render(<App />)
    expect(screen.getByText('FundGuard')).toBeTruthy()
    expect(screen.getByText(/Omega Payout Coordinator/i)).toBeTruthy()
  })

  it('navigates to Recipients & Teams tab and displays add form', () => {
    render(<App />)
    const recTabBtn = screen.getByRole('button', { name: /Recipients & Teams/i })
    fireEvent.click(recTabBtn)
    expect(screen.getByRole('heading', { name: /Add Recipient Team/i })).toBeTruthy()
    expect(screen.getByRole('heading', { level: 2, name: /Recipient Directory/i })).toBeTruthy()
  })

  it('navigates to Award Rules & Calculator tab and displays calculator', () => {
    render(<App />)
    const policyTabBtn = screen.getByRole('button', { name: /Award Rules & Calculator/i })
    fireEvent.click(policyTabBtn)
    expect(screen.getByRole('heading', { name: /Track 02 Proportional Award Calculator/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /Active Governance Policies/i })).toBeTruthy()
  })

  it('navigates to Payout Batches tab and displays draft form', () => {
    render(<App />)
    const batchTabBtn = screen.getByRole('button', { name: /Payout Batches/i })
    fireEvent.click(batchTabBtn)
    expect(screen.getByRole('heading', { name: /Draft Payout Batch/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /Authorize & Settle Batch/i })).toBeTruthy()
  })

  it('navigates to Treasury & Audit Trail tab and displays ledger breakdown', () => {
    render(<App />)
    const auditTabBtn = screen.getByRole('button', { name: /Treasury & Audit Trail/i })
    fireEvent.click(auditTabBtn)
    expect(screen.getByRole('heading', { name: /Treasury Ledger Breakdown/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /Cryptographic Audit Trail/i })).toBeTruthy()
  })

  it('allows toggling settlement network mode', () => {
    render(<App />)
    const selectEl = screen.getByDisplayValue(/Stellar Testnet/i)
    expect(selectEl).toBeTruthy()
    fireEvent.change(selectEl, { target: { value: 'simulated' } })
    expect(screen.getByDisplayValue(/Local Simulation/i)).toBeTruthy()
  })
})

describe('Independent Public Views & Access Controls', () => {
  beforeEach(() => {
    window.scrollTo = vi.fn()
  })

  afterEach(() => {
    cleanup()
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('renders the public landing page with value proposition and actions', () => {
    render(<App initialView="landing" />)
    expect(screen.getByText(/Automated, Verifiable Program Disbursements/i)).toBeTruthy()
    expect(screen.getAllByRole('button', { name: /Explore Live Demo/i }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: /Sign In/i }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: /Create Account|Create Free Account/i }).length).toBeGreaterThan(0)
  })

  it('navigates to signup page and ensures demo page is NOT accessible from signup', () => {
    render(<App initialView="signup" />)
    expect(screen.getByRole('heading', { name: /Create Your Account/i })).toBeTruthy()
    expect(screen.getByPlaceholderText(/alex@organization.com/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: /Back to Home/i })).toBeTruthy()
    // Verify demo access is strictly omitted
    expect(screen.queryByText(/Explore Live Demo/i)).toBeNull()
    expect(screen.queryByText(/Demo Mode/i)).toBeNull()
  })

  it('navigates to login page and ensures demo page is NOT accessible from login', () => {
    render(<App initialView="login" />)
    expect(screen.getByRole('heading', { name: /Sign In to FundGuard/i })).toBeTruthy()
    expect(screen.getByPlaceholderText(/name@organization.com/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: /Back to Home/i })).toBeTruthy()
    // Verify demo access is strictly omitted
    expect(screen.queryByText(/Explore Live Demo/i)).toBeNull()
    expect(screen.queryByText(/Demo Mode/i)).toBeNull()
  })

  it('renders the live demo environment banner and allows exiting back to home', () => {
    render(<App initialView="demo" />)
    expect(screen.getByText(/Demo Mode/i)).toBeTruthy()
    expect(screen.getByText(/Live Stellar Testnet Sandbox/i)).toBeTruthy()
    const exitBtn = screen.getByRole('button', { name: /Exit Demo/i })
    expect(exitBtn).toBeTruthy()
    fireEvent.click(exitBtn)
    expect(screen.getByText(/Automated, Verifiable Program Disbursements/i)).toBeTruthy()
  })
})

describe('Account Creation & Workspace Isolation Flow', () => {
  beforeEach(() => {
    window.scrollTo = vi.fn()
    localStorage.clear()
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url, options) => {
      if (url.includes('/auth/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            user: {
              id: 'user-bob-99',
              email: 'bob@alphaventures.com',
              full_name: 'Bob Alpha',
              organization_id: 'org-alpha-99',
              organization_name: 'Alpha Ventures',
              role: 'sponsor'
            },
            default_competition_id: 'comp-alpha-1',
            token: 'test-token-bob'
          })
        })
      }
      if (url.includes('/competitions?organization_id=org-alpha-99')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: 'comp-alpha-1',
              name: 'Alpha Ventures Prize Fund',
              description: 'Primary isolated workspace for Alpha Ventures',
              organization_id: 'org-alpha-99',
              network: 'stellar-testnet'
            }
          ])
        })
      }
      if (url.includes('/treasury/comp-alpha-1')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            competition_id: 'comp-alpha-1',
            currency: 'XLM',
            total_fund_base_units: 17000000000,
            paid_base_units: 1000000000,
            available_base_units: 16000000000,
            carry_forward_reserve_base_units: 16000000000,
            reserved_base_units: 0,
            proposed_base_units: 0
          })
        })
      }
      if (url.includes('/recipients')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        })
      }
      if (url.includes('/batches')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        })
      }
      if (url.includes('/audit')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        })
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    }))
  })

  afterEach(() => {
    cleanup()
    localStorage.clear()
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('completes signup and isolates user dashboard with correct disbursement and remaining balance', async () => {
    render(<App initialView="signup" />)

    // Fill registration form
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Alex Morgan/i), { target: { value: 'Bob Alpha' } })
    fireEvent.change(screen.getByPlaceholderText(/alex@organization\.com/i), { target: { value: 'bob@alphaventures.com' } })
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. Apex Global Foundation/i), { target: { value: 'Alpha Ventures' } })
    fireEvent.change(screen.getByPlaceholderText(/Choose a secure password/i), { target: { value: 'alphaPass123' } })

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))

    // Wait for transition to user dashboard
    await vi.waitFor(() => {
      expect(screen.getByText('Bob Alpha')).toBeTruthy()
      expect(screen.getAllByText(/Alpha Ventures/i).length).toBeGreaterThan(0)
    })

    // Verify workspace select only contains Alpha Ventures Prize Fund
    expect(screen.getAllByText('Alpha Ventures Prize Fund').length).toBeGreaterThan(0)
    expect(screen.queryByText('FundGuard Test Challenge')).toBeNull()

    // Verify financial metrics are clearly labeled as Settled Disbursements and Remaining Available Balance
    expect(screen.getByText(/Total Settled Disbursements/i)).toBeTruthy()
    expect(screen.getByText(/Remaining Available Balance/i)).toBeTruthy()
    expect(screen.getByText('100.00 XLM')).toBeTruthy()
    expect(screen.getAllByText('1,600.00 XLM').length).toBeGreaterThan(0)
  })
})


