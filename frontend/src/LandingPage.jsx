import React from 'react'

export default function LandingPage({ onNavigate }) {
  const scrollToSection = (id) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="landing-page">
      {/* Top Navigation */}
      <header className="landing-nav">
        <div className="landing-brand" onClick={() => onNavigate('landing')}>
          <div className="brand-mark">FG</div>
          <span className="landing-brand-title">FundGuard</span>
          <span className="landing-brand-tag">Enterprise Escrow</span>
        </div>

        <nav className="landing-nav-links">
          <button className="landing-nav-link" onClick={() => scrollToSection('how-it-works')}>
            Workflow
          </button>
          <button className="landing-nav-link" onClick={() => scrollToSection('features')}>
            Capabilities
          </button>
          <button className="landing-nav-link" onClick={() => scrollToSection('architecture')}>
            Security & Compliance
          </button>
          <a
            className="landing-nav-link"
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
            API Reference
          </a>
        </nav>

        <div className="landing-nav-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => onNavigate('demo')}
            title="Try interactive demo sandbox"
          >
            Explore Live Demo
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => onNavigate('login')}
          >
            Sign In
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => onNavigate('signup')}
          >
            Create Account
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="hero-pill">
          Enterprise Programmatic Disbursements &amp; Escrow Infrastructure
        </div>

        <h1 className="hero-title">
          Automated, Verifiable Program Disbursements{' '}
          <span className="hero-title-accent">Built for Scale</span>
        </h1>

        <p className="hero-subtitle">
          Eliminate manual spreadsheets, delayed international wires, and payout disputes.
          FundGuard empowers foundations, organizations, and ecosystem funds with rule-governed
          escrow, proportional reserve protection, and sub-5-second multi-recipient settlement on Stellar.
        </p>

        <div className="hero-actions">
          <button
            className="btn-hero-primary"
            onClick={() => onNavigate('signup')}
          >
            Create Free Account
          </button>
          <button
            className="btn-hero-secondary"
            onClick={() => onNavigate('demo')}
          >
            Explore Live Demo (No Signup Required)
          </button>
        </div>

        {/* Commercial Grade Performance Metrics */}
        <div className="hero-metrics-strip">
          <div>
            <div className="metric-item-val">Sub-5s</div>
            <div className="metric-item-lbl">Global Settlement Speed</div>
          </div>
          <div>
            <div className="metric-item-val">100%</div>
            <div className="metric-item-lbl">Deterministic Stroops Precision</div>
          </div>
          <div>
            <div className="metric-item-val">0</div>
            <div className="metric-item-lbl">Intermediary Banking Fees</div>
          </div>
        </div>
      </section>

      {/* 3-Step Process Section */}
      <section className="landing-section" id="how-it-works">
        <div className="section-head">
          <div className="section-eyebrow">Enterprise Workflow</div>
          <h2 className="section-title">How FundGuard Powers Programmatic Payouts</h2>
          <p className="section-desc">
            A reliable, transparent pipeline engineered for grant programs, prize competitions, and milestone disbursement operations.
          </p>
        </div>

        <div className="steps-grid">
          <div className="step-card">
            <div className="step-number">1</div>
            <h3 className="step-title">Deposit & Configure Escrow Policies</h3>
            <p className="step-desc">
              Allocate program capital into dedicated custody vaults with pre-set governance thresholds. Capital remains protected until verified release conditions are met.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number">2</div>
            <h3 className="step-title">Verify Recipients & Proportional Benchmarks</h3>
            <p className="step-desc">
              Perform automated on-chain preflight checks on recipient accounts. Dynamic proportional release formulas adjust disbursement ratios automatically, protecting unearned reserve capital.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number">3</div>
            <h3 className="step-title">Instant Atomic Batch Settlement</h3>
            <p className="step-desc">
              Authorize multi-recipient disbursements in a single transaction. Stellar native atomic batching delivers funds directly to all recipient wallets in seconds with cryptographic receipts.
            </p>
          </div>
        </div>
      </section>

      {/* Core Capabilities Grid */}
      <section className="landing-section" id="features">
        <div className="section-head">
          <div className="section-eyebrow">Core Capabilities</div>
          <h2 className="section-title">Engineered for Financial Rigor & Transparency</h2>
          <p className="section-desc">
            Replace subjective manual disbursement processes with mathematical guarantees and immutable audit trails.
          </p>
        </div>

        <div className="features-grid">
          <div className="feature-box">
            <h3 className="feature-box-title">Mathematical Proportional Capital Protection</h3>
            <p className="feature-box-desc">
              Eliminate all-or-nothing payout risk. If a program targets 10 milestone winners but only 4 qualify, 40% releases to recipients while 60% automatically rolls into a protected reserve for future disbursements.
            </p>
          </div>

          <div className="feature-box">
            <h3 className="feature-box-title">High-Throughput Native Settlement</h3>
            <p className="feature-box-desc">
              Ultra-low network fees and rapid finality. FundGuard automatically handles first-time account creation and direct balance credits in a unified transaction pipeline.
            </p>
          </div>

          <div className="feature-box">
            <h3 className="feature-box-title">Cryptographic Audit Proofs</h3>
            <p className="feature-box-desc">
              Every state transition — policy updates, recipient verifications, batch authorizations, and on-chain broadcasts — generates a SHA-256 hashed audit log with UTC timestamps for sponsors and compliance teams.
            </p>
          </div>

          <div className="feature-box">
            <h3 className="feature-box-title">Tenant Workspace Segregation</h3>
            <p className="feature-box-desc">
              Multi-tenant architecture enforces strict boundaries between organizations. Public visitors and other tenants cannot view confidential recipient directories or internal balance ledgers.
            </p>
          </div>
        </div>
      </section>

      {/* Security & Financial Determinism */}
      <section className="landing-section" id="architecture">
        <div className="section-head">
          <div className="section-eyebrow">Security & Determinism</div>
          <h2 className="section-title">Provable Accounting with Zero Float Drift</h2>
          <p className="section-desc">
            Designed to institutional standards with integer-based accounting and multi-step execution validation.
          </p>
        </div>

        <div className="features-grid">
          <div className="feature-box">
            <h3 className="feature-box-title">Integer Stroops Arithmetic</h3>
            <p className="feature-box-desc">
              All financial balances and allocations are computed exclusively in integer base units (1 XLM = 10,000,000 stroops). Rounded remainders are deterministically attributed to the reserve, avoiding rounding errors.
            </p>
          </div>

          <div className="feature-box">
            <h3 className="feature-box-title">Multi-Step Preflight Authorization</h3>
            <p className="feature-box-desc">
              Batches require an explicit validation preflight check against custodial balances and address integrity before an approval hash can unlock on-chain execution.
            </p>
          </div>
        </div>
      </section>

      {/* Commercial Call to Action Banner */}
      <div className="landing-cta-banner">
        <h2 className="landing-cta-title">Ready to Modernize Your Program Disbursements?</h2>
        <p className="landing-cta-desc">
          Launch your organization workspace today or explore the live testnet sandbox to see instant Stellar settlement in action.
        </p>
        <div className="landing-cta-actions">
          <button
            className="btn btn-primary"
            style={{ padding: '12px 28px', fontSize: '15px' }}
            onClick={() => onNavigate('signup')}
          >
            Create Free Account
          </button>
          <button
            className="btn btn-secondary"
            style={{ padding: '12px 28px', fontSize: '15px' }}
            onClick={() => onNavigate('demo')}
          >
            Explore Live Demo
          </button>
        </div>
      </div>

      {/* Product Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-text">
            <strong>FundGuard Treasury Systems</strong> — Enterprise Programmatic Disbursements &amp; Escrow Infrastructure
          </div>
          <div className="landing-footer-links">
            <button className="landing-footer-link" onClick={() => onNavigate('landing')} style={{ background: 'none', border: 'none' }}>
              Home
            </button>
            <button className="landing-footer-link" onClick={() => onNavigate('demo')} style={{ background: 'none', border: 'none' }}>
              Demo Sandbox
            </button>
            <button className="landing-footer-link" onClick={() => onNavigate('login')} style={{ background: 'none', border: 'none' }}>
              Sign In
            </button>
            <button className="landing-footer-link" onClick={() => onNavigate('signup')} style={{ background: 'none', border: 'none' }}>
              Register
            </button>
            <a
              className="landing-footer-link"
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              API Reference
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
