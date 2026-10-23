import React, { useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000/api/v1'

export default function LoginPage({ onNavigate, onLoginSuccess }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMsg('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password
        })
      })

      const data = await res.json()
      if (!res.ok) {
        const msg = data.detail
          ? Array.isArray(data.detail)
            ? data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
            : data.detail
          : 'Invalid email or password.'
        throw new Error(msg)
      }

      // Persist auth and notify parent
      localStorage.setItem('fundguard_user', JSON.stringify(data.user))
      localStorage.setItem('fundguard_token', data.token)
      if (data.default_competition_id) {
        localStorage.setItem('fundguard_active_competition', data.default_competition_id)
      }

      onLoginSuccess(data)
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed')
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
            <h2 className="auth-card-title">Sign In to FundGuard</h2>
            <p className="auth-card-desc">
              Access your competition workspaces and escrow treasury.
            </p>
          </div>

          {errorMsg && <div className="auth-alert-error">{errorMsg}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label>Work Email</label>
              <input
                type="email"
                required
                placeholder="name@organization.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label>Password</label>
              <input
                type="password"
                required
                placeholder="Enter your password"
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
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="auth-card-footer">
            Don't have an account?{' '}
            <button type="button" onClick={() => onNavigate('signup')}>
              Create one
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
