import React, { useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000/api/v1'

export default function SignupPage({ onNavigate, onRegisterSuccess }) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [orgName, setOrgName] = useState('')
  const [role, setRole] = useState('organizer')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMsg('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim(),
          organization_name: orgName.trim(),
          role,
          password
        })
      })

      const data = await res.json()
      if (!res.ok) {
        const msg = data.detail
          ? Array.isArray(data.detail)
            ? data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
            : data.detail
          : 'Registration failed. Please check your information.'
        throw new Error(msg)
      }

      // Persist auth and notify parent
      localStorage.setItem('fundguard_user', JSON.stringify(data.user))
      localStorage.setItem('fundguard_token', data.token)
      if (data.default_competition_id) {
        localStorage.setItem('fundguard_active_competition', data.default_competition_id)
      }

      onRegisterSuccess(data)
    } catch (err) {
      setErrorMsg(err.message || 'Network error during registration')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-view">
      <header className="auth-nav">
        <div
          className="landing-brand"
          onClick={() => onNavigate('landing')}
          style={{ cursor: 'pointer' }}
        >
          <div className="brand-mark">FG</div>
          <span className="landing-brand-title">FundGuard</span>
        </div>
        <button
          className="auth-nav-back"
          onClick={() => onNavigate('landing')}
        >
          Back to Home
        </button>
      </header>

      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-card-head">
            <h2 className="auth-card-title">Create Your Account</h2>
            <p className="auth-card-desc">
              Start managing transparent, rule-governed prize distributions and Stellar payouts.
            </p>
          </div>

          {errorMsg && <div className="auth-alert-error">{errorMsg}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group" style={{ marginBottom: '14px' }}>
              <label>Full Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Alex Morgan"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '14px' }}>
              <label>Work Email</label>
              <input
                type="email"
                required
                placeholder="alex@organization.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '14px' }}>
              <label>Organization or Foundation Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Apex Global Foundation"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '14px' }}>
              <label>Account Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="organizer">Program Administrator</option>
                <option value="sponsor">Fund Sponsor / Foundation Lead</option>
                <option value="judge">Reviewer / Finance Auditor</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: '20px' }}>
              <label>Password (min. 6 characters)</label>
              <input
                type="password"
                required
                minLength={6}
                placeholder="Choose a secure password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px' }}
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="auth-card-footer">
            Already have an account?{' '}
            <button type="button" onClick={() => onNavigate('login')}>
              Sign In
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
