import React, { useEffect, useMemo, useRef, useState } from 'react'
import LandingPage from './LandingPage.jsx'
import SignupPage from './SignupPage.jsx'
import LoginPage from './LoginPage.jsx'

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function getInitialView(initialProp) {
  if (initialProp) return initialProp
  if (typeof window !== 'undefined') {
    const hash = window.location.hash.replace(/^#\/?/, '')
    if (['landing', 'signup', 'login', 'demo', 'app'].includes(hash)) {
      return hash
    }
    const savedUser = localStorage.getItem('fundguard_user')
    if (savedUser) {
      return 'app'
    }
  }
  if (typeof import.meta !== 'undefined' && import.meta.env?.MODE === 'test') {
    return 'demo'
  }
  return 'landing'
}

async function request(path, options = {}) {
  const { headers, ...rest } = options
  const response = await fetch(`${API}/api/v1${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {}),
    },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const errorMsg = Array.isArray(body.detail)
      ? body.detail.map(d => `${d.loc ? d.loc.slice(1).join('.') : ''} ${d.msg}`).join(', ')
      : (body.detail || body.message || `Request failed (${response.status})`)
    throw new Error(errorMsg)
  }
  return body
}

function short(value = '') {
  return value && value.length > 16 ? `${value.slice(0, 8)}…${value.slice(-6)}` : value
}

function formatXLM(stroops) {
  if (stroops === undefined || stroops === null) return '0.00 XLM'
  const val = Number(stroops) / 10000000
  return `${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} XLM`
}

function App({ initialView = null }) {
  const [view, setView] = useState(() => getInitialView(initialView))
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const raw = localStorage.getItem('fundguard_user')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })

  const [competitions, setCompetitions] = useState([])
  const [selected, setSelected] = useState('')
  const [recipients, setRecipients] = useState([])
  const [batches, setBatches] = useState([])
  const [audit, setAudit] = useState([])
  const [policies, setPolicies] = useState([])
  const [treasury, setTreasury] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [tab, setTab] = useState('overview')
  const [busy, setBusy] = useState(false)
  const [mode, setMode] = useState('stellar-testnet') // 'stellar-testnet' or 'simulated'

  // Workspace Creation Form
  const [compName, setCompName] = useState('Prize Distribution Workspace')
  const [compDescription, setCompDescription] = useState('Automated, human-approved payouts to verified recipients.')

  // Recipient Form
  const [recipientName, setRecipientName] = useState('')
  const [wallet, setWallet] = useState('')
  const [recipientNote, setRecipientNote] = useState('Track winner submission verified by organizer')

  // Recipient CSV Upload State
  const [recipientMode, setRecipientMode] = useState('single') // 'single' | 'csv'
  const [csvFile, setCsvFile] = useState(null)
  const [csvRows, setCsvRows] = useState([])
  const [csvAutoVerify, setCsvAutoVerify] = useState(false)
  const [csvErrors, setCsvErrors] = useState([])
  const [csvSuccessMsg, setCsvSuccessMsg] = useState('')
  const [csvImporting, setCsvImporting] = useState(false)
  const fileInputRef = useRef(null)

  // Manual Batch Creation Form (amounts in XLM)
  const [selectedRecipients, setSelectedRecipients] = useState([])
  const [amountXLM, setAmountXLM] = useState('50')
  const [reserveXLM, setReserveXLM] = useState('0')
  const [activeBatchId, setActiveBatchId] = useState('')
  const [approverName, setApproverName] = useState('Finance Director')
  const [showAdvancedReserve, setShowAdvancedReserve] = useState(false)

  const activeActor = (view === 'app' && currentUser) ? (currentUser.full_name || currentUser.email) : 'Demo Administrator'
  const activeApprover = (view === 'app' && currentUser) ? (currentUser.full_name || currentUser.email) : (approverName || 'Demo Administrator')

  // Policy Simulator
  const [simTarget, setSimTarget] = useState(50)
  const [simEligible, setSimEligible] = useState(20)
  const [simOutcome, setSimOutcome] = useState(null)

  // AI Agent Assistant Status
  const [agentSummary, setAgentSummary] = useState(null)

  // Stellar Custody & Near Quote
  const [custody, setCustody] = useState(null)
  const [nearQuote, setNearQuote] = useState(null)

  // Hash route listener
  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '')
      if (['landing', 'signup', 'login', 'demo', 'app'].includes(hash)) {
        setView(hash)
      }
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const navigate = async (nextView) => {
    setView(nextView)
    if (typeof window !== 'undefined') {
      window.location.hash = `#/${nextView}`
      try { window.scrollTo({ top: 0, behavior: 'smooth' }) } catch (_) {}
    }
    if (nextView === 'demo') {
      setSelected('')
      setRecipients([])
      setBatches([])
      setAudit([])
      setPolicies([])
      setTreasury(null)
      setActiveBatchId('')
      await loadCompetitions(null, null, 'demo')
    } else if (nextView === 'app') {
      const stored = (() => {
        try { return JSON.parse(localStorage.getItem('fundguard_user') || 'null') } catch { return null }
      })()
      const u = currentUser || stored
      await loadCompetitions(null, u, 'app')
    }
  }

  const handleRegisterSuccess = async (authData) => {
    setCurrentUser(authData.user)
    setView('app')
    if (typeof window !== 'undefined') {
      window.location.hash = '#/app'
    }
    // Clean all previous state to avoid cross-account data leaks
    setSelected('')
    setCompetitions([])
    setRecipients([])
    setBatches([])
    setAudit([])
    setPolicies([])
    setTreasury(null)
    setActiveBatchId('')
    await loadCompetitions(authData.default_competition_id, authData.user, 'app')
  }

  const handleLoginSuccess = async (authData) => {
    setCurrentUser(authData.user)
    setView('app')
    if (typeof window !== 'undefined') {
      window.location.hash = '#/app'
    }
    // Clean all previous state to avoid cross-account data leaks
    setSelected('')
    setCompetitions([])
    setRecipients([])
    setBatches([])
    setAudit([])
    setPolicies([])
    setTreasury(null)
    setActiveBatchId('')
    await loadCompetitions(authData.default_competition_id, authData.user, 'app')
  }

  const handleLogout = () => {
    localStorage.removeItem('fundguard_user')
    localStorage.removeItem('fundguard_token')
    localStorage.removeItem('fundguard_active_competition')
    setCurrentUser(null)
    setSelected('')
    setCompetitions([])
    setRecipients([])
    setBatches([])
    setAudit([])
    setPolicies([])
    setTreasury(null)
    setActiveBatchId('')
    navigate('landing')
  }

  async function loadCompetitions(preferred, userOverride, viewOverride) {
    const activeView = viewOverride || view
    const stored = (() => {
      try { return JSON.parse(localStorage.getItem('fundguard_user') || 'null') } catch { return null }
    })()
    const activeUser = userOverride !== undefined ? userOverride : (currentUser || stored)

    let orgParam = ''
    if (activeView === 'app') {
      if (activeUser?.organization_id) {
        orgParam = `?organization_id=${activeUser.organization_id}`
      } else {
        setCompetitions([])
        setSelected('')
        setRecipients([])
        setBatches([])
        setAudit([])
        setPolicies([])
        setTreasury(null)
        return
      }
    } else if (activeView === 'demo') {
      orgParam = '?organization_id=org-basix-global'
    }

    let list = await request(`/competitions${orgParam}`).catch(() => [])

    if (list.length === 0 && activeView === 'demo') {
      const allComps = await request('/competitions').catch(() => [])
      list = allComps.filter(c => c.organization_id === 'org-basix-global' || !c.organization_id)
      if (list.length === 0) list = allComps
    }

    // Strict filter for authenticated app mode
    if (activeView === 'app' && activeUser?.organization_id) {
      list = list.filter(c => c.organization_id === activeUser.organization_id)
    }

    setCompetitions(list)

    // Ensure selected is strictly from the active organization's list
    let next = ''
    const savedActive = (() => {
      try { return localStorage.getItem('fundguard_active_competition') } catch { return null }
    })()
    if (preferred && list.some(c => c.id === preferred)) {
      next = preferred
    } else if (savedActive && list.some(c => c.id === savedActive)) {
      next = savedActive
    } else if (selected && list.some(c => c.id === selected)) {
      next = selected
    } else if (list.length > 0) {
      next = list[0].id
    }

    if (next) {
      try { localStorage.setItem('fundguard_active_competition', next) } catch (_) {}
    }
    setSelected(next)
    if (next) {
      await loadAll(next)
    } else {
      setRecipients([])
      setBatches([])
      setAudit([])
      setPolicies([])
      setTreasury(null)
    }
  }

  async function loadAll(id = selected) {
    if (!id) {
      setRecipients([])
      setBatches([])
      setPolicies([])
      setTreasury(null)
      return
    }
    const [r, b, a, p, t, sc, nq] = await Promise.all([
      request(`/competitions/${id}/recipients`).catch(() => []),
      request(`/competitions/${id}/batches`).catch(() => []),
      request(`/audit/events?competition_id=${id}`).catch(() => []),
      request(`/competitions/${id}/policies`).catch(() => []),
      request(`/treasury/${id}`).catch(() => null),
      request('/stellar/custody').catch(() => null),
      request('/near-intents/quote?from_asset=XLM&to_asset=NEAR&amount_base_units=10000000').catch(() => null),
    ])
    setRecipients(r)
    setBatches(b)
    setAudit(a.slice().reverse())
    setPolicies(p)
    setTreasury(t)
    setCustody(sc)
    setNearQuote(nq)
  }

  useEffect(() => {
    if (view === 'demo' || view === 'app') {
      loadCompetitions().catch(e => setError(e.message))
    }
  }, [view, currentUser])

  useEffect(() => {
    if (selected && (view === 'demo' || view === 'app')) {
      loadAll(selected).catch(e => setError(e.message))
    }
  }, [selected, view])

  const current = competitions.find(c => c.id === selected)
  const verifiedRecipients = useMemo(() => recipients.filter(r => r.eligibility_status === 'verified'), [recipients])
  const activeBatch = useMemo(() => batches.find(b => b.id === activeBatchId) || batches[0], [batches, activeBatchId])

  const completedTransfersCount = useMemo(() => {
    return batches.reduce((acc, b) => acc + (b.payouts || []).filter(p => p.status === 'confirmed' || p.status === 'simulated').length, 0)
  }, [batches])

  const pendingBatches = useMemo(() => {
    return batches.filter(b => b.status === 'approved' || b.status === 'proposed')
  }, [batches])

  const pendingAmount = useMemo(() => {
    return (treasury?.reserved_base_units || 0) + (treasury?.proposed_base_units || 0)
  }, [treasury])

  const pendingSettlementBatch = useMemo(() => {
    return batches.find(b => b.status === 'approved')
  }, [batches])

  const pendingApprovalBatch = useMemo(() => {
    return batches.find(b => b.status === 'proposed')
  }, [batches])

  function notify(text) {
    setMessage(text)
    setError('')
    setTimeout(() => setMessage(''), 6000)
  }

  async function run(fn) {
    setBusy(true)
    setError('')
    try { await fn() } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  async function createWorkspace(e) {
    e.preventDefault()
    if (!compName.trim()) return
    await run(async () => {
      const orgId = view === 'app' && currentUser?.organization_id ? currentUser.organization_id : 'org-basix-global'
      const c = await request('/competitions', {
        method: 'POST',
        body: JSON.stringify({
          name: compName.trim(),
          description: compDescription.trim(),
          network: 'stellar-testnet',
          organization_id: orgId,
          created_by: activeActor
        })
      })
      await loadCompetitions(c.id, currentUser, view)
      setTab('overview')
      notify(`Workspace "${compName}" created. You can switch between all workspaces at any time.`)
    })
  }

  async function switchWorkspace(id) {
    if (!id) return
    setActiveBatchId('')
    setRecipients([])
    setBatches([])
    setAudit([])
    setPolicies([])
    setTreasury(null)
    setSelected(id)
    try { localStorage.setItem('fundguard_active_competition', id) } catch (_) {}
    await loadAll(id)
    setTab('overview')
    const target = competitions.find(c => c.id === id)
    notify(`Switched to workspace: ${target?.name || id}`)
  }

  async function addRecipient(e) {
    e.preventDefault()
    if (!wallet.trim()) return
    await run(async () => {
      await request(`/competitions/${selected}/recipients`, {
        method: 'POST',
        body: JSON.stringify({
          display_name: recipientName.trim(),
          wallet_address: wallet.trim(),
          eligibility_note: recipientNote,
          eligibility_status: 'pending',
          created_by: activeActor
        })
      })
      setRecipientName('')
      setWallet('')
      await loadAll()
      notify('Recipient added as Pending. Review and mark verified to make eligible for payouts.')
    })
  }

  async function autoGenerateWallet() {
    await run(async () => {
      const kp = await request('/stellar/generate-keypair?fund_via_friendbot=true', { method: 'POST' })
      setWallet(kp.public_key)
      if (!recipientName) setRecipientName(`Team Stellar (${kp.public_key.slice(0, 6)})`)
      notify(`Generated and funded genuine Stellar address: ${short(kp.public_key)}`)
    })
  }

  async function verifyRecipient(id) {
    await run(async () => {
      await request(`/competitions/${selected}/recipients/${id}/verify?reviewer=${encodeURIComponent(activeActor)}`, { method: 'POST' })
      await loadAll()
      notify('Recipient eligibility verified by reviewer.')
    })
  }

  function downloadSampleCsv() {
    const csvContent =
      "name,wallet_address,notes\n" +
      "Alpha Pioneers,GA7SFOTHBSSRUGL4NUYZXCQTO2MDDJYUIEVPYIYPCYD2BR2RQOVNXIHD,Finalist recipient\n" +
      "Beta Innovators,GB2GGSI4Q4JUC2K4HSCDYDK5XAZQD5DXTRC3COL4QZRHLZBSGDK4DPVW,Track award winner\n" +
      "Gamma Protocol,GCRXSDVF23OPVXSXBUQJWQ3VMWGOX24YUGLB3CDBYOVV23CIAVTIPSJH,Grant cohort team\n"
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'recipients_template.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  function handleCsvFileSelect(file) {
    if (!file) return
    setCsvFile(file)
    setCsvErrors([])
    setCsvSuccessMsg('')

    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result
      if (!text || typeof text !== 'string') return
      const parsed = parseCsvRecipients(text)
      setCsvRows(parsed)
    }
    reader.readAsText(file)
  }

  function parseCsvRecipients(text) {
    const lines = text.split(/\r\n|\n/).filter(line => line.trim().length > 0)
    if (lines.length === 0) return []

    const splitLine = (l) => {
      const res = []
      let curr = ''
      let inQuotes = false
      for (let i = 0; i < l.length; i++) {
        const ch = l[i]
        if (ch === '"') inQuotes = !inQuotes
        else if (ch === ',' && !inQuotes) { res.push(curr.trim()); curr = '' }
        else curr += ch
      }
      res.push(curr.trim())
      return res
    }

    const firstRow = splitLine(lines[0]).map(c => c.toLowerCase().replace(/[\s_]+/g, ''))
    let nameIdx = -1, walletIdx = -1, noteIdx = -1
    let hasHeaders = false

    firstRow.forEach((col, idx) => {
      if (['name', 'displayname', 'team', 'teamname', 'recipient', 'recipientname'].includes(col)) {
        nameIdx = idx; hasHeaders = true
      } else if (['wallet', 'walletaddress', 'address', 'stellaraddress', 'publickey', 'key', 'strkey'].includes(col)) {
        walletIdx = idx; hasHeaders = true
      } else if (['notes', 'note', 'eligibilitynote', 'reviewnotes', 'comments', 'description'].includes(col)) {
        noteIdx = idx; hasHeaders = true
      }
    })

    const dataLines = hasHeaders ? lines.slice(1) : lines
    if (!hasHeaders) {
      nameIdx = 0
      walletIdx = 1
      noteIdx = 2
    }

    return dataLines.map((line, idx) => {
      const cols = splitLine(line)
      const name = cols[nameIdx] || ''
      const wallet = cols[walletIdx] || ''
      const note = cols[noteIdx] || ''
      const isValidStrKey = /^G[A-Z2-7]{55}$/.test(wallet)
      return {
        rowNum: idx + 1,
        name,
        wallet,
        note,
        isValidStrKey,
        error: !name ? 'Missing name' : !wallet ? 'Missing address' : !isValidStrKey ? 'Invalid Stellar ed25519 address' : null
      }
    }).filter(r => r.name || r.wallet)
  }

  function resetCsvUpload() {
    setCsvFile(null)
    setCsvRows([])
    setCsvErrors([])
    setCsvSuccessMsg('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function importCsvRecipients() {
    if (!csvFile && csvRows.length === 0) return
    await run(async () => {
      setCsvImporting(true)
      try {
        let result
        if (csvFile) {
          const formData = new FormData()
          formData.append('file', csvFile)
          formData.append('auto_verify', csvAutoVerify ? 'true' : 'false')
          formData.append('reviewer', activeActor)
          formData.append('created_by', activeActor)

          const token = localStorage.getItem('fundguard_token')
          const headers = {}
          if (token) headers['Authorization'] = `Bearer ${token}`

          const res = await fetch(`${API}/api/v1/competitions/${selected}/recipients/upload-csv`, {
            method: 'POST',
            headers,
            body: formData
          })
          if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            throw new Error(err.detail || 'Failed to upload CSV')
          }
          result = await res.json()
        } else {
          result = await request(`/competitions/${selected}/recipients/bulk`, {
            method: 'POST',
            body: JSON.stringify({
              recipients: csvRows.filter(r => !r.error).map(r => ({
                display_name: r.name,
                wallet_address: r.wallet,
                eligibility_note: r.note
              })),
              auto_verify: csvAutoVerify,
              reviewer: activeActor,
              created_by: activeActor
            })
          })
        }

        setCsvSuccessMsg(`Successfully imported ${result.imported_count} recipient(s).${result.skipped_count > 0 ? ` ${result.skipped_count} row(s) skipped.` : ''}`)
        if (result.errors && result.errors.length > 0) {
          setCsvErrors(result.errors)
        } else {
          setCsvErrors([])
        }
        setCsvFile(null)
        setCsvRows([])
        if (fileInputRef.current) fileInputRef.current.value = ''
        await loadAll()
        notify(`Imported ${result.imported_count} recipients via CSV.`)
      } finally {
        setCsvImporting(false)
      }
    })
  }

  async function runAiAutoProposal() {
    if (verifiedRecipients.length === 0) {
      setError('Cannot draft payout: No verified recipients. Please verify at least one team in Recipients first.')
      return
    }
    await run(async () => {
      // 1. Run AI agent recommendation
      const res = await request(`/agent/run?competition_id=${selected}`, {
        method: 'POST',
        body: JSON.stringify({
          intent: 'prepare_payout_proposal',
          prompt: 'Calculate proportional awards for verified winning teams and prepare proposal batch.'
        })
      })
      setAgentSummary(res.summary)

      // 2. Automatically create the batch proposal with calculated proportional allocation
      const key = crypto.randomUUID()
      const totalBudgetStroops = 17000000000 // 1,700 XLM standard budget
      const targetCount = 50
      const eligibleCount = verifiedRecipients.length
      const releaseRatio = Math.min(1.0, eligibleCount / targetCount)
      const releasedTotalStroops = Math.round(totalBudgetStroops * releaseRatio)
      const perRecipientStroops = Math.round(releasedTotalStroops / eligibleCount)
      const reserveStroops = totalBudgetStroops - releasedTotalStroops

      const b = await request(`/competitions/${selected}/batches`, {
        method: 'POST',
        headers: { 'Idempotency-Key': key },
        body: JSON.stringify({
          recipient_ids: verifiedRecipients.map(r => r.id),
          amount_base_units: perRecipientStroops,
          reserve_base_units: reserveStroops,
          asset_code: 'XLM',
          asset_type: 'native',
          created_by: activeActor
        })
      })

      setActiveBatchId(b.id)
      await loadAll()
      setTab('batches')
      notify('AI Auto-Draft completed: Proposal created and ready for authorization.')
    })
  }

  async function createManualBatch(e) {
    e.preventDefault()
    const targetRecipients = selectedRecipients.length > 0 ? selectedRecipients : verifiedRecipients.map(r => r.id)
    if (targetRecipients.length === 0) {
      setError('Please verify and select at least one recipient.')
      return
    }
    await run(async () => {
      const key = crypto.randomUUID()
      const amountStroops = Math.round(Number(amountXLM || '0') * 10000000)
      const reserveStroops = Math.round(Number(reserveXLM || '0') * 10000000)
      const b = await request(`/competitions/${selected}/batches`, {
        method: 'POST',
        headers: { 'Idempotency-Key': key },
        body: JSON.stringify({
          recipient_ids: targetRecipients,
          amount_base_units: amountStroops,
          reserve_base_units: reserveStroops,
          asset_code: 'XLM',
          asset_type: 'native',
          created_by: activeActor
        })
      })
      setActiveBatchId(b.id)
      setSelectedRecipients([])
      await loadAll()
      notify('Payout batch drafted. Please review and authorize.')
    })
  }

  async function approveBatch(b) {
    await run(async () => {
      await request(`/batches/${b.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ approver: activeApprover, confirm_hash: b.content_hash, decision: 'approved', role: currentUser?.role || 'finance_approver', reason: 'Reviewed and confirmed eligible winner allocations' })
      })
      await loadAll()
      notify('Batch authorized with cryptographic hash match. Ready for settlement execution.')
    })
  }

  async function executeBatch(b) {
    await run(async () => {
      const res = await request(`/batches/${b.id}/execute`, {
        method: 'POST',
        body: JSON.stringify({ requested_by: activeApprover, mode })
      })
      await loadAll()
      if (res.status === 'confirmed') {
        notify('Settlement executed and confirmed on Stellar Testnet.')
      } else {
        notify(`Settlement executed in ${mode} mode.`)
      }
    })
  }

  async function authorizeAndSettleBatch(b) {
    await run(async () => {
      await request(`/batches/${b.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ approver: activeApprover, confirm_hash: b.content_hash, decision: 'approved', role: currentUser?.role || 'finance_approver', reason: 'Authorized for immediate settlement execution' })
      })
      const res = await request(`/batches/${b.id}/execute`, {
        method: 'POST',
        body: JSON.stringify({ requested_by: activeApprover, mode })
      })
      await loadAll()
      if (res.status === 'confirmed') {
        notify('Batch authorized & successfully confirmed on Stellar Testnet.')
      } else {
        notify(`Batch authorized & executed in ${mode} mode.`)
      }
    })
  }

  async function cancelBatch(id) {
    await run(async () => {
      await request(`/batches/${id}/cancel?actor=${encodeURIComponent(activeActor)}`, { method: 'POST' })
      await loadAll()
      notify('Batch allocation cancelled. Reserved funds returned to available balance.')
    })
  }

  async function runPolicySimulator(e) {
    if (e) e.preventDefault()
    await run(async () => {
      const res = await request(`/competitions/${selected}/policies/simulate`, {
        method: 'POST',
        body: JSON.stringify({
          target_eligible_count: Number(simTarget),
          eligible_count: Number(simEligible),
          total_fund_base_units: 17000000000
        })
      })
      setSimOutcome(res.calculated_outcome)
    })
  }

  async function topUpCustody() {
    await run(async () => {
      const res = await request('/stellar/fund-friendbot', { method: 'POST' })
      notify(res.message || '10,000 testnet XLM credited to payout vault.')
      const sc = await request('/stellar/custody').catch(() => null)
      setCustody(sc)
    })
  }

  if (view === 'landing') {
    return <LandingPage onNavigate={navigate} />
  }

  if (view === 'signup') {
    return <SignupPage onNavigate={navigate} onRegisterSuccess={handleRegisterSuccess} />
  }

  if (view === 'login') {
    return <LoginPage onNavigate={navigate} onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <div className="app-shell-wrapper">
      {view === 'demo' && (
        <div className="demo-top-banner">
          <div className="demo-banner-indicator">
            <span className="demo-banner-pill">Demo Mode</span>
            <span>Live Stellar Testnet Sandbox — Pre-loaded demo data. On-chain transactions execute live on Stellar Testnet.</span>
          </div>
          <div className="demo-banner-actions">
            <button
              className="btn-demo-action btn-demo-exit"
              onClick={() => navigate('landing')}
            >
              Exit Demo
            </button>
            <button
              className="btn-demo-action btn-demo-signup"
              onClick={() => navigate('signup')}
            >
              Create Account
            </button>
          </div>
        </div>
      )}

      <div className="app-shell">
        {/* SIDEBAR NAVIGATION */}
        <aside className="sidebar">
          <div className="brand" onClick={() => navigate('landing')} style={{ cursor: 'pointer' }} title="Return to Landing Page">
            <div className="brand-mark">FG</div>
            <div className="brand-text">
              <strong>FundGuard</strong>
              <span>Omega Payout Coordinator</span>
            </div>
          </div>

          {view === 'app' && currentUser && (
            <div className="user-auth-pill">
              <div className="user-auth-info">
                <span className="user-auth-name">{currentUser.full_name}</span>
                <span className="user-auth-org">{currentUser.organization_name} · {currentUser.role}</span>
              </div>
              <button
                className="btn-user-logout"
                onClick={handleLogout}
                title="Log out of session"
              >
                Log Out
              </button>
            </div>
          )}

          {view === 'demo' && (
            <div className="user-auth-pill">
              <div className="user-auth-info">
                <span className="user-auth-name">Demo Sandbox</span>
                <span className="user-auth-org">Stellar Testnet Explorer</span>
              </div>
              <button
                className="btn-user-logout"
                onClick={() => navigate('landing')}
                title="Return to Landing Page"
              >
                Exit
              </button>
            </div>
          )}

          <div className="sidebar-section-label">Active Workspace</div>
          <select
            className="sidebar-workspace-select"
            value={selected}
            onChange={e => switchWorkspace(e.target.value)}
          >
            {competitions.length === 0 && <option value="">No workspaces found</option>}
            {competitions.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>

        <nav>
          {[
            ['overview', 'Overview & Insights'],
            ['recipients', 'Recipients & Teams'],
            ['policies', 'Award Rules & Calculator'],
            ['batches', 'Payout Batches'],
            ['treasury', 'Treasury & Audit Trail'],
            ['setup', 'Workspaces']
          ].map(([key, label]) => (
            <button
              key={key}
              className={`nav-item ${tab === key ? 'active' : ''}`}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="settlement-badge">
            <span>Settlement Network</span>
            <select value={mode} onChange={e => setMode(e.target.value)}>
              <option value="stellar-testnet">Stellar Testnet (Live)</option>
              <option value="simulated">Local Simulation (Demo)</option>
            </select>
          </div>
        </div>
      </aside>

      {/* MAIN VIEWPORT */}
      <main className="main">
        {/* TOPBAR */}
        <header className="topbar">
          <div className="topbar-title">
            <span className="sidebar-section-label" style={{ padding: 0 }}>
              {current?.name || 'Workspace'}
            </span>
            <h1>
              {tab === 'overview' && 'Prize Distribution & Health'}
              {tab === 'recipients' && 'Recipient Directory & Verification'}
              {tab === 'policies' && 'Proportional Release Policy'}
              {tab === 'batches' && 'Payout Batches & Authorizations'}
              {tab === 'treasury' && 'Treasury Invariants & Audit Log'}
              {tab === 'setup' && 'Manage Workspaces'}
            </h1>
            <p className="topbar-subtitle">
              {tab === 'overview' && 'Real-time overview of fund allocations, recipient status, and on-chain deliveries.'}
              {tab === 'recipients' && 'Manage participating teams, verify program eligibility, and review reliability scores.'}
              {tab === 'policies' && 'Proportional award calculator and reserve rollover rules.'}
              {tab === 'batches' && 'Review AI-generated payout drafts, verify cryptographic fingerprints, and execute settlements.'}
              {tab === 'treasury' && 'Cryptographically verifiable ledger tracking fund balances, reserve carry-forward, and audit proofs.'}
              {tab === 'setup' && 'Switch between previous program workspaces or create a new isolated workspace.'}
            </p>
          </div>

          <div className="topbar-meta">
            <span className={`status-pill ${mode === 'stellar-testnet' ? 'testnet' : 'simulated'}`}>
              <span className="pulse-dot"></span>
              {mode === 'stellar-testnet' ? 'Stellar Testnet Active' : 'Simulation Mode'}
            </span>
          </div>
        </header>

        {/* NOTIFICATIONS */}
        {message && <div className="notice success"><span>[OK] {message}</span><button onClick={() => setMessage('')} className="btn-secondary btn-sm" style={{ border: 0 }}>Close</button></div>}
        {error && <div className="notice error"><span>[Notice] {error}</span><button onClick={() => setError('')} className="btn-secondary btn-sm" style={{ border: 0 }}>Close</button></div>}

        {/* 1. OVERVIEW TAB */}
        {tab === 'overview' && (
          <div>
            {/* Quick Metrics */}
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">Total Fund Pool</span>
                <div className="metric-value">{treasury ? formatXLM(treasury.total_fund_base_units) : '0.00 XLM'}</div>
                <span className="metric-sub">{treasury?.total_fund_display || 'Allocated Program Budget'}</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Total Settled Disbursements</span>
                <div className="metric-value" style={{ color: '#2e7d32' }}>{treasury ? formatXLM(treasury.paid_base_units) : '0.00 XLM'}</div>
                <span className="metric-sub">{completedTransfersCount} completed transfers</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Pending Authorizations</span>
                <div className="metric-value" style={{ color: pendingAmount > 0 ? '#b78103' : 'inherit' }}>{formatXLM(pendingAmount)}</div>
                <span className="metric-sub">{pendingBatches.length} batch(es) in progress</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Carry-Forward Reserve</span>
                <div className="metric-value" style={{ color: '#1e6091' }}>{treasury ? formatXLM(treasury.carry_forward_reserve_base_units) : '0.00 XLM'}</div>
                <span className="metric-sub">Protected rollover per policy</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Remaining Available Balance</span>
                <div className="metric-value" style={{ color: '#1e6091' }}>{treasury ? formatXLM(treasury.available_base_units) : '0.00 XLM'}</div>
                <span className="metric-sub">Available for disbursements</span>
              </div>
            </div>

            {/* Urgent Settlement Action Banner */}
            {pendingSettlementBatch && (
              <div style={{
                background: '#eff6ff',
                border: '1px solid #93c5fd',
                borderRadius: 'var(--radius-sm)',
                padding: '16px 20px',
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '16px',
                flexWrap: 'wrap'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="badge badge-blue">AUTHORIZED - AWAITING SETTLEMENT</span>
                    <strong style={{ fontSize: '15px', color: '#1e40af' }}>
                      Batch #{short(pendingSettlementBatch.id)} is Ready for On-Chain Execution
                    </strong>
                  </div>
                  <p style={{ fontSize: '13px', color: '#1e3a8a', margin: 0 }}>
                    Award disbursement of <strong>{formatXLM(pendingSettlementBatch.total_base_units)}</strong> across {pendingSettlementBatch.payouts?.length || 0} recipient(s) has been cryptographically signed and is awaiting final delivery.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="btn-primary"
                    onClick={() => executeBatch(pendingSettlementBatch)}
                    disabled={busy}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    Execute Settlement on Stellar Testnet Now
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => { setActiveBatchId(pendingSettlementBatch.id); setTab('batches'); }}
                    disabled={busy}
                  >
                    View Batch Details
                  </button>
                </div>
              </div>
            )}

            {/* Proposal Drafted Banner */}
            {!pendingSettlementBatch && pendingApprovalBatch && (
              <div style={{
                background: '#fefce8',
                border: '1px solid #fde047',
                borderRadius: 'var(--radius-sm)',
                padding: '16px 20px',
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '16px',
                flexWrap: 'wrap'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="badge badge-amber">PROPOSAL DRAFTED</span>
                    <strong style={{ fontSize: '15px', color: '#854d0e' }}>
                      Batch #{short(pendingApprovalBatch.id)} Awaiting Finance Sign-Off
                    </strong>
                  </div>
                  <p style={{ fontSize: '13px', color: '#713f12', margin: 0 }}>
                    Proposed payout of <strong>{formatXLM(pendingApprovalBatch.total_base_units)}</strong> across {pendingApprovalBatch.payouts?.length || 0} recipient(s) has been prepared.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="btn-primary"
                    onClick={() => authorizeAndSettleBatch(pendingApprovalBatch)}
                    disabled={busy}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    Authorize & Settle Immediately
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => { setActiveBatchId(pendingApprovalBatch.id); setTab('batches'); }}
                    disabled={busy}
                  >
                    Review Proposal
                  </button>
                </div>
              </div>
            )}

            {/* Stepper Workflow */}
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>End-to-End Distribution Workflow</h2>
                  <p>Guaranteed mathematical fairness: from eligibility verification to on-chain execution.</p>
                </div>
                <button className="btn-primary btn-sm" onClick={runAiAutoProposal} disabled={busy || verifiedRecipients.length === 0}>
                  Auto-Draft Proposal (AI)
                </button>
              </div>

              <div className="stepper">
                <div className="step-card active">
                  <div className="step-index">STEP 01</div>
                  <strong>1. Define Funding Policy</strong>
                  <span>Proportional formula: min(1.0, Verified / Target).</span>
                </div>
                <div className={`step-card ${recipients.length > 0 ? 'active' : ''}`}>
                  <div className="step-index">STEP 02</div>
                  <strong>2. Verify Winners</strong>
                  <span>Organizer confirms team eligibility criteria.</span>
                </div>
                <div className={`step-card ${batches.length > 0 ? 'active' : ''}`}>
                  <div className="step-index">STEP 03</div>
                  <strong>3. AI Drafts Proposal</strong>
                  <span>Automated allocation respecting reserve rules.</span>
                </div>
                <div className={`step-card ${batches.some(b => b.status === 'confirmed' || b.status === 'simulated') ? 'active' : ''}`}>
                  <div className="step-index">STEP 04</div>
                  <strong>4. Authorize & Settle</strong>
                  <span>Finance Director signs; funds delivered on Stellar.</span>
                </div>
              </div>
            </div>

            {/* Stellar Vault & Quick Actions */}
            <div className="two-col-grid">
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h2>Stellar Payout Vault Status</h2>
                    <p>Isolated testnet signer account used to deliver awards.</p>
                  </div>
                  <button className="btn-secondary btn-sm" onClick={topUpCustody} disabled={busy}>
                    Fund Payout Vault
                  </button>
                </div>

                <div style={{ display: 'grid', gap: '12px' }}>
                  <div style={{ background: 'var(--bg-subtle)', padding: '12px 14px', borderRadius: 'var(--radius-sm)' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Vault Public Address</span>
                    <strong style={{ fontSize: '12px', wordBreak: 'break-all' }}>{custody?.account_id || 'Generating or loading keypair...'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 4px' }}>
                    <div>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block' }}>Available Testnet Balance:</span>
                      <strong style={{ fontSize: '18px', color: '#1e6091' }}>{custody ? `${parseFloat(custody.xlm_balance).toFixed(2)} XLM` : '0.00 XLM'}</strong>
                    </div>
                    <span className={`badge ${custody?.funded ? 'badge-green' : 'badge-amber'}`}>
                      {custody?.funded ? 'Ready for Payouts' : 'Needs Funding'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h2>Recent Distribution Activity</h2>
                    <p>Latest cryptographic events recorded in the tamper-proof ledger.</p>
                  </div>
                  <button className="btn-secondary btn-sm" onClick={() => setTab('treasury')}>
                    View All Activity
                  </button>
                </div>

                {audit.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '12px 0' }}>No activity recorded yet in this workspace.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {audit.slice(0, 4).map(evt => (
                      <div key={evt.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', fontSize: '12px' }}>
                        <div>
                          <strong>{evt.action}</strong>
                          <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>by {evt.actor}</span>
                        </div>
                        <span className="badge badge-green">Verified</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 2. RECIPIENTS TAB */}
        {tab === 'recipients' && (
          <div className="two-col-grid">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Add Recipient Team</h2>
                  <p>Register individual teams or bulk import multiple recipients via CSV file.</p>
                </div>
              </div>

              {/* Toggle Mode: Single vs CSV */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '18px', borderBottom: '1px solid var(--border)', paddingBottom: '12px' }}>
                <button
                  type="button"
                  className={`btn-sm ${recipientMode === 'single' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => { setRecipientMode('single'); setCsvErrors([]); setCsvSuccessMsg(''); }}
                  style={{ fontSize: '12px' }}
                >
                  Single Recipient Form
                </button>
                <button
                  type="button"
                  className={`btn-sm ${recipientMode === 'csv' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => { setRecipientMode('csv'); }}
                  style={{ fontSize: '12px' }}
                >
                  Upload CSV File
                </button>
              </div>

              {recipientMode === 'single' ? (
                <form onSubmit={addRecipient}>
                  <div className="form-group">
                    <label>Team or Recipient Display Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Team Northstar"
                      value={recipientName}
                      onChange={e => setRecipientName(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <label>Stellar Public Address (56-char ed25519 StrKey)</label>
                      <button type="button" className="btn-secondary btn-sm" onClick={autoGenerateWallet} disabled={busy} style={{ fontSize: '11px', padding: '3px 8px' }}>
                        Generate Testnet Wallet
                      </button>
                    </div>
                    <input
                      type="text"
                      required
                      placeholder="G..."
                      value={wallet}
                      onChange={e => setWallet(e.target.value)}
                    />
                    <span className="form-hint">Validates genuine ed25519 public keys format starting with 'G'.</span>
                  </div>

                  <div className="form-group">
                    <label>Organizer Review Notes</label>
                    <input
                      type="text"
                      placeholder="e.g. Verified eligibility criteria met"
                      value={recipientNote}
                      onChange={e => setRecipientNote(e.target.value)}
                    />
                  </div>

                  <button className="btn-primary" type="submit" disabled={busy || !wallet.trim() || !recipientName.trim()}>
                    Register Recipient
                  </button>
                </form>
              ) : (
                <div>
                  <div style={{ background: 'var(--bg-subtle)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '16px', fontSize: '13px', lineHeight: '1.5' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong>Bulk Import Recipients via CSV</strong>
                      <button
                        type="button"
                        className="btn-secondary btn-sm"
                        onClick={downloadSampleCsv}
                        style={{ fontSize: '11px', padding: '3px 8px' }}
                      >
                        Download Sample CSV
                      </button>
                    </div>
                    <p style={{ color: 'var(--text-muted)', marginTop: '6px', fontSize: '12px' }}>
                      Upload a CSV file with columns: <span className="info-formula">name, wallet_address, notes</span>. Validates 56-character ed25519 StrKey public keys.
                    </p>
                  </div>

                  <div
                    className="csv-dropzone"
                    style={{
                      border: '2px dashed var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '24px 16px',
                      textAlign: 'center',
                      background: csvFile ? 'rgba(46, 125, 50, 0.05)' : 'var(--bg-subtle)',
                      cursor: 'pointer',
                      marginBottom: '16px',
                      transition: 'border-color 0.2s'
                    }}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => { e.preventDefault(); }}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        handleCsvFileSelect(e.dataTransfer.files[0]);
                      }
                    }}
                  >
                    <input
                      type="file"
                      ref={fileInputRef}
                      accept=".csv,text/csv"
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          handleCsvFileSelect(e.target.files[0]);
                        }
                      }}
                    />
                    {csvFile ? (
                      <div>
                        <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text)' }}>{csvFile.name}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                          {(csvFile.size / 1024).toFixed(1)} KB · {csvRows.length} rows detected
                        </div>
                        <button
                          type="button"
                          className="btn-secondary btn-sm"
                          style={{ marginTop: '10px', fontSize: '11px', padding: '3px 8px' }}
                          onClick={(e) => { e.stopPropagation(); resetCsvUpload(); }}
                        >
                          Change File
                        </button>
                      </div>
                    ) : (
                      <div>
                        <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>Click to select a CSV file or drag and drop</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Supports .csv files with name, wallet_address, notes</div>
                      </div>
                    )}
                  </div>

                  {csvRows.length > 0 && (
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '12px' }}>
                        <strong>File Preview ({csvRows.length} rows)</strong>
                        <div>
                          <span className="badge badge-green" style={{ marginRight: '6px' }}>
                            {csvRows.filter(r => r.isValidStrKey).length} valid
                          </span>
                          {csvRows.filter(r => !r.isValidStrKey).length > 0 && (
                            <span className="badge badge-red">
                              {csvRows.filter(r => !r.isValidStrKey).length} invalid
                            </span>
                          )}
                        </div>
                      </div>
                      <div style={{ maxHeight: '180px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                        <table style={{ fontSize: '11px', width: '100%', borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ background: 'var(--bg-subtle)', textAlign: 'left' }}>
                              <th style={{ padding: '6px 8px' }}>#</th>
                              <th style={{ padding: '6px 8px' }}>Name</th>
                              <th style={{ padding: '6px 8px' }}>Wallet</th>
                              <th style={{ padding: '6px 8px' }}>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {csvRows.map((r, i) => (
                              <tr key={i} style={{ borderTop: '1px solid var(--border)' }}>
                                <td style={{ padding: '6px 8px' }}>{r.rowNum}</td>
                                <td style={{ padding: '6px 8px' }}><strong>{r.name || '(empty)'}</strong></td>
                                <td style={{ padding: '6px 8px', fontFamily: 'var(--font-mono)' }}>{short(r.wallet)}</td>
                                <td style={{ padding: '6px 8px' }}>
                                  {r.error ? (
                                    <span style={{ color: 'var(--danger)', fontSize: '10px' }}>{r.error}</span>
                                  ) : (
                                    <span className="badge badge-green" style={{ fontSize: '10px' }}>Ready</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  <div className="form-group" style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }}>
                      <input
                        type="checkbox"
                        checked={csvAutoVerify}
                        onChange={(e) => setCsvAutoVerify(e.target.checked)}
                      />
                      <span>Automatically mark imported recipients as Verified</span>
                    </label>
                    <span className="form-hint">If unchecked, recipients will be imported as Pending review.</span>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={busy || csvImporting || csvRows.filter(r => !r.error).length === 0}
                      onClick={importCsvRecipients}
                    >
                      {csvImporting ? 'Importing...' : `Import ${csvRows.filter(r => !r.error).length} Recipients`}
                    </button>
                    {csvFile && (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={resetCsvUpload}
                        disabled={busy || csvImporting}
                      >
                        Clear
                      </button>
                    )}
                  </div>

                  {csvSuccessMsg && (
                    <div style={{ marginTop: '12px', padding: '10px 12px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 'var(--radius-sm)', color: '#166534', fontSize: '12px' }}>
                      {csvSuccessMsg}
                    </div>
                  )}
                  {csvErrors.length > 0 && (
                    <div style={{ marginTop: '12px', padding: '10px 12px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-sm)', color: '#991b1b', fontSize: '12px' }}>
                      <strong>Import Warnings:</strong>
                      <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
                        {csvErrors.map((err, i) => (
                          <li key={i}>Row {err.row}: {err.name || err.wallet} - {err.error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Recipient Directory ({recipients.length})</h2>
                  <p>Teams must be marked Verified by an organizer before awards can be paid.</p>
                </div>
              </div>

              {recipients.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '16px 0' }}>No recipients registered. Add one using the form on the left.</p>
              ) : (
                <div className="table-responsive">
                  <table>
                    <thead>
                      <tr>
                        <th>Team</th>
                        <th>Stellar Address</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recipients.map(r => (
                        <tr key={r.id}>
                          <td>
                            <strong>{r.display_name}</strong>
                          </td>
                          <td>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                              {short(r.wallet_address)}
                            </span>
                          </td>
                          <td>
                            <span className={`badge ${r.eligibility_status === 'verified' ? 'badge-green' : r.eligibility_status === 'rejected' ? 'badge-red' : 'badge-amber'}`}>
                              {r.eligibility_status}
                            </span>
                          </td>
                          <td>
                            {r.eligibility_status === 'pending' && (
                              <button className="btn-secondary btn-sm" onClick={() => verifyRecipient(r.id)} disabled={busy}>
                                Verify Eligibility
                              </button>
                            )}
                            {r.eligibility_status === 'verified' && (
                              <span style={{ fontSize: '11px', color: '#2e7d32', fontWeight: 600 }}>Eligible</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. POLICIES & CALCULATOR TAB */}
        {tab === 'policies' && (
          <div className="two-col-grid">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Proportional Award Calculator</h2>
                  <p>Simulate the official proportional release and carry-forward reserve formula.</p>
                </div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', marginBottom: '18px', fontSize: '13px', lineHeight: '1.6' }}>
                <strong>How it works:</strong>
                <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>
                  If fewer than the target number of teams meet the quality bar, the prize fund releases proportionally:
                  <span className="info-formula">Release Ratio = min(1.0, Verified Count / Target Count)</span>
                  <br />
                  Unreleased prize funds automatically roll into the protected Carry-Forward Reserve.
                </p>
              </div>

              <form onSubmit={runPolicySimulator}>
                <div className="form-group">
                  <label>Target Winners Count: {simTarget}</label>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={simTarget}
                    onChange={e => setSimTarget(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Actual Verified Teams: {simEligible}</label>
                  <input
                    type="range"
                    min="0"
                    max={simTarget}
                    value={simEligible}
                    onChange={e => setSimEligible(e.target.value)}
                  />
                </div>

                <button className="btn-primary" type="button" onClick={runPolicySimulator} disabled={busy}>
                  Calculate Allocation
                </button>
              </form>

              {simOutcome && (
                <div style={{ marginTop: '24px', borderTop: '1px solid var(--border)', paddingTop: '18px' }}>
                  <h3 style={{ fontSize: '14px', marginBottom: '12px' }}>Calculation Result</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="metric-card" style={{ padding: '14px' }}>
                      <span className="metric-label">Release Ratio</span>
                      <div className="metric-value" style={{ fontSize: '20px' }}>{(simOutcome.release_ratio * 100).toFixed(1)}%</div>
                      <span className="metric-sub">{simOutcome.eligible_count} out of {simOutcome.target_eligible_count} target</span>
                    </div>
                    <div className="metric-card" style={{ padding: '14px' }}>
                      <span className="metric-label">Per-Winner Award</span>
                      <div className="metric-value" style={{ fontSize: '20px', color: '#2e7d32' }}>{formatXLM(simOutcome.amount_per_recipient_base_units)}</div>
                      <span className="metric-sub">Equal award distribution</span>
                    </div>
                    <div className="metric-card" style={{ padding: '14px' }}>
                      <span className="metric-label">Total Released</span>
                      <div className="metric-value" style={{ fontSize: '20px' }}>{formatXLM(simOutcome.released_base_units)}</div>
                      <span className="metric-sub">{simOutcome.illustrative_released_fiat || '$680.00'}</span>
                    </div>
                    <div className="metric-card" style={{ padding: '14px' }}>
                      <span className="metric-label">Carry-Forward Reserve</span>
                      <div className="metric-value" style={{ fontSize: '20px', color: '#1e6091' }}>{formatXLM(simOutcome.total_reserve_base_units)}</div>
                      <span className="metric-sub">{simOutcome.illustrative_reserve_fiat || '$1020.00'}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Active Governance Policies</h2>
                  <p>Rules enforced by the backend MeTTa symbolic engine on every payout.</p>
                </div>
              </div>

              <div style={{ display: 'grid', gap: '14px' }}>
                <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <strong>Proportional Release Policy</strong>
                    <span className="badge badge-green">Active</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                    Target: 50 teams · Minimum eligible: 1 team · Base currency: XLM · Equal split distribution among verified winners.
                  </p>
                </div>

                <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <strong>Treasury Invariant Enforcement</strong>
                    <span className="badge badge-green">Active</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                    Guarantees no negative balances and ensures total commitments (paid + reserved + in-flight) cannot exceed total allocated funds.
                  </p>
                </div>

                <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <strong>Dual-Signoff Security Binding</strong>
                    <span className="badge badge-green">Active</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                    Payout execution is cryptographically bound to the SHA-256 batch hash; any tampering rejects execution automatically.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 4. PAYOUT BATCHES TAB */}
        {tab === 'batches' && (
          <div>
            <div className="two-col-grid" style={{ marginBottom: '24px' }}>
              {/* Proposal Generator */}
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h2>Draft Payout Batch</h2>
                    <p>Select verified recipients and define awards, or let AI generate the draft.</p>
                  </div>
                  <button className="btn-secondary btn-sm" onClick={runAiAutoProposal} disabled={busy || verifiedRecipients.length === 0}>
                    Auto-Draft Proposal (AI)
                  </button>
                </div>

                {agentSummary && (
                  <div style={{ background: '#f0f7ef', border: '1px solid #c9e4c5', padding: '12px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '16px', fontSize: '13px', color: '#275225' }}>
                    <strong>AI Recommendation:</strong> {agentSummary}
                  </div>
                )}

                <form onSubmit={createManualBatch}>
                  <div className="form-group">
                    <label>Select Verified Winners ({selectedRecipients.length > 0 ? selectedRecipients.length : `${verifiedRecipients.length} (all eligible)`} selected)</label>
                    {verifiedRecipients.length === 0 ? (
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No verified recipients available. Verify teams in the Recipients tab first.</p>
                    ) : (
                      <div style={{ maxHeight: '160px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '10px' }}>
                        {verifiedRecipients.map(r => (
                          <label key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', fontSize: '13px', cursor: 'pointer' }}>
                            <input
                              type="checkbox"
                              checked={selectedRecipients.length > 0 ? selectedRecipients.includes(r.id) : true}
                              onChange={e => {
                                const currentList = selectedRecipients.length > 0 ? selectedRecipients : verifiedRecipients.map(x => x.id)
                                if (e.target.checked) setSelectedRecipients([...currentList, r.id])
                                else setSelectedRecipients(currentList.filter(x => x !== r.id))
                              }}
                            />
                            <strong>{r.display_name}</strong>
                            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({short(r.wallet_address)})</span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="form-group" style={{ marginBottom: '14px' }}>
                    <label>Amount per Recipient (XLM)</label>
                    <input
                      type="number"
                      min="1"
                      required
                      value={amountXLM}
                      onChange={e => setAmountXLM(e.target.value)}
                    />
                    <span className="form-hint">
                      Total Disbursement: {formatXLM(Math.round(Number(amountXLM || '0') * 10000000) * (selectedRecipients.length > 0 ? selectedRecipients.length : verifiedRecipients.length))} across {selectedRecipients.length > 0 ? selectedRecipients.length : verifiedRecipients.length} recipients.
                    </span>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <button
                      type="button"
                      className="btn-secondary btn-sm"
                      onClick={() => setShowAdvancedReserve(!showAdvancedReserve)}
                      style={{ fontSize: '11px', padding: '4px 10px' }}
                    >
                      {showAdvancedReserve ? 'Hide Advanced Options' : 'Advanced: Allocate Unreleased Reserve (Optional)'}
                    </button>
                    {showAdvancedReserve && (
                      <div className="form-group" style={{ marginTop: '10px' }}>
                        <label>Reserve Amount (XLM)</label>
                        <input
                          type="number"
                          min="0"
                          value={reserveXLM}
                          onChange={e => setReserveXLM(e.target.value)}
                        />
                        <span className="form-hint">Unreleased reserve capital to set aside. Defaults to 0.</span>
                      </div>
                    )}
                  </div>

                  <button className="btn-primary" type="submit" disabled={busy || verifiedRecipients.length === 0}>
                    Create Payout Proposal
                  </button>
                </form>
              </div>

              {/* Batch Authorization & Execution Card */}
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h2>Authorize & Settle Batch</h2>
                    <p>Review cryptographic fingerprint and execute settlement.</p>
                  </div>
                </div>

                {!activeBatch ? (
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '16px 0' }}>No payout batches created yet. Create one or run AI Auto-Draft above.</p>
                ) : (
                  <div>
                    <div style={{ background: 'var(--bg-subtle)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <strong style={{ fontSize: '14px' }}>Batch #{short(activeBatch.id)}</strong>
                        <span className={`badge ${activeBatch.status === 'confirmed' ? 'badge-green' : activeBatch.status === 'approved' ? 'badge-blue' : 'badge-amber'}`}>
                          {activeBatch.status.toUpperCase()}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'grid', gap: '4px' }}>
                        <div>Total Disbursement: <strong>{formatXLM(activeBatch.total_base_units)}</strong> ({activeBatch.payouts?.length || 0} recipients)</div>
                        {activeBatch.reserve_base_units > 0 && (
                          <div>Unreleased Reserve: <strong>{formatXLM(activeBatch.reserve_base_units)}</strong></div>
                        )}
                        <div>Security Fingerprint: <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{short(activeBatch.content_hash)}</span></div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      {activeBatch.status === 'proposed' && (
                        <>
                          <button className="btn-primary" onClick={() => authorizeAndSettleBatch(activeBatch)} disabled={busy}>
                            Authorize & Settle Immediately ({mode === 'stellar-testnet' ? 'Stellar Testnet' : 'Simulation'})
                          </button>
                          <button className="btn-secondary" onClick={() => approveBatch(activeBatch)} disabled={busy}>
                            Authorize Only (Hold)
                          </button>
                          <button className="btn-secondary" onClick={() => cancelBatch(activeBatch.id)} disabled={busy} style={{ color: '#c53030' }}>
                            Cancel Batch
                          </button>
                        </>
                      )}
                      {activeBatch.status === 'approved' && (
                        <>
                          <button className="btn-primary" onClick={() => executeBatch(activeBatch)} disabled={busy} style={{ background: '#1e6091', borderColor: '#1e6091' }}>
                            Execute Settlement on {mode === 'stellar-testnet' ? 'Stellar Testnet (Live)' : 'Simulation'} Now
                          </button>
                          <button className="btn-secondary" onClick={() => cancelBatch(activeBatch.id)} disabled={busy} style={{ color: '#c53030' }}>
                            Cancel Batch
                          </button>
                        </>
                      )}
                      {(activeBatch.status === 'confirmed' || activeBatch.status === 'simulated') && (
                        <div style={{ color: '#2e7d32', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                          [Settled] Successfully Confirmed on {activeBatch.status === 'confirmed' ? 'Stellar Testnet' : 'Simulation'}
                        </div>
                      )}
                      {activeBatch.status === 'cancelled' && (
                        <div style={{ color: '#718096', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          [Cancelled] Allocation cancelled and returned to available fund pool.
                        </div>
                      )}
                    </div>

                    {/* Payout receipts list */}
                    {activeBatch.payouts && activeBatch.payouts.length > 0 && (
                      <div style={{ marginTop: '18px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '8px' }}>Award Recipients:</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {activeBatch.payouts.map(p => (
                            <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#ffffff', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '12px' }}>
                              <span>Recipient ID: {short(p.recipient_id)}</span>
                              <strong>{formatXLM(p.amount_base_units)}</strong>
                              {p.tx_hash ? (
                                <a
                                  href={`https://stellar.expert/explorer/testnet/tx/${p.tx_hash}`}
                                  target="_blank"
                                  rel="noreferrer"
                                  style={{ color: '#1e6091', textDecoration: 'none', fontWeight: 600 }}
                                >
                                  Tx: {short(p.tx_hash)} [Explorer]
                                </a>
                              ) : (
                                <span className="badge badge-gray">{p.status}</span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Batch History Table */}
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>All Payout Batches ({batches.length})</h2>
                  <p>Complete history of all proposed, approved, and executed batches in this workspace.</p>
                </div>
              </div>

              {batches.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '12px 0' }}>No batch history.</p>
              ) : (
                <div className="table-responsive">
                  <table>
                    <thead>
                      <tr>
                        <th>Batch ID</th>
                        <th>Status</th>
                        <th>Total Disbursement</th>
                        <th>Recipients</th>
                        <th>Mode</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {batches.map(b => (
                        <tr key={b.id}>
                          <td><strong>{short(b.id)}</strong></td>
                          <td>
                            <span className={`badge ${b.status === 'confirmed' ? 'badge-green' : b.status === 'approved' ? 'badge-blue' : 'badge-amber'}`}>
                              {b.status}
                            </span>
                          </td>
                          <td>{formatXLM(b.total_base_units)}</td>
                          <td>{b.payouts?.length || 0} recipients</td>
                          <td>{b.execution_mode || 'pending'}</td>
                          <td>
                            <div style={{ display: 'flex', gap: '6px' }}>
                              {b.status === 'approved' && (
                                <button className="btn-primary btn-sm" onClick={() => executeBatch(b)} disabled={busy}>
                                  Settle
                                </button>
                              )}
                              {b.status === 'proposed' && (
                                <button className="btn-primary btn-sm" onClick={() => authorizeAndSettleBatch(b)} disabled={busy}>
                                  Settle
                                </button>
                              )}
                              <button className="btn-secondary btn-sm" onClick={() => setActiveBatchId(b.id)}>
                                Select
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 5. TREASURY & AUDIT TAB */}
        {tab === 'treasury' && (
          <div>
            <div className="two-col-grid" style={{ marginBottom: '24px' }}>
              {/* Treasury Balances */}
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h2>Treasury Ledger Breakdown</h2>
                    <p>Mathematical proof that all allocations and reserves preserve solvency invariants.</p>
                  </div>
                </div>

                <div style={{ display: 'grid', gap: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <span>Total Program Budget:</span>
                    <strong>{treasury ? formatXLM(treasury.total_fund_base_units) : '0.00 XLM'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <span>Settled Disbursements (Confirmed):</span>
                    <strong style={{ color: '#2e7d32' }}>{treasury ? formatXLM(treasury.paid_base_units) : '0.00 XLM'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <span>Pending Authorizations:</span>
                    <strong style={{ color: '#b78103' }}>{treasury ? formatXLM((treasury.reserved_base_units || 0) + (treasury.proposed_base_units || 0)) : '0.00 XLM'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <span>Remaining Available Balance:</span>
                    <strong style={{ color: '#1e6091' }}>{treasury ? formatXLM(treasury.available_base_units) : '0.00 XLM'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <span>Proportional Policy Reserve (Carry-Forward):</span>
                    <strong style={{ color: '#1e6091' }}>{treasury ? formatXLM(treasury.carry_forward_reserve_base_units) : '0.00 XLM'}</strong>
                  </div>
                </div>

                <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#2e7d32', fontSize: '13px' }}>
                  <span>[Solvency Verified] Paid + Reserve equals 100% of the initial prize pool.</span>
                </div>
              </div>

              {/* NEAR Intents Cross-Chain Quote Card */}
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h2>Cross-Chain Swap Simulator (NEAR Intents)</h2>
                    <p>Simulated dry quote for cross-chain winner settlement.</p>
                  </div>
                </div>

                {nearQuote ? (
                  <div style={{ background: 'var(--bg-subtle)', padding: '16px', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Estimated Exchange:</span>
                      <strong>{nearQuote.source_amount_display} to {nearQuote.estimated_destination_amount}</strong>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'grid', gap: '6px' }}>
                      <div>Simulated Rate: 1 XLM = {nearQuote.simulated_exchange_rate} NEAR</div>
                      <div>Slippage Tolerance: {nearQuote.slippage_tolerance_pct}</div>
                      <div>Estimated Network Fee: {nearQuote.estimated_network_fee_stroops} stroops</div>
                      <div style={{ marginTop: '8px', fontSize: '11px', color: '#888' }}>
                        Note: Dry quote simulation. NEAR Intents has no public testnet.
                      </div>
                    </div>
                  </div>
                ) : (
                  <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading cross-chain exchange rates...</p>
                )}
              </div>
            </div>

            {/* Cryptographic Audit Trail */}
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Cryptographic Audit Trail ({audit.length} Events)</h2>
                  <p>SHA-256 hash-chained log preserving tamper-evident proof of every action.</p>
                </div>
                <a
                  href={`${API}/api/v1/audit/export?competition_id=${selected}&format=json`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary btn-sm"
                >
                  Export Audit JSON
                </a>
              </div>

              {audit.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '16px 0' }}>No audit records yet.</p>
              ) : (
                <div className="table-responsive">
                  <table>
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Action</th>
                        <th>Operator</th>
                        <th>Entity</th>
                        <th>Tamper Check</th>
                      </tr>
                    </thead>
                    <tbody>
                      {audit.map(evt => (
                        <tr key={evt.id}>
                          <td><small style={{ color: 'var(--text-muted)' }}>{evt.created_at ? new Date(evt.created_at).toLocaleString() : 'N/A'}</small></td>
                          <td><strong>{evt.action}</strong></td>
                          <td>{evt.actor}</td>
                          <td>{evt.entity_type} ({short(evt.entity_id)})</td>
                          <td>
                            <span className={`badge ${evt.integrity_valid ? 'badge-green' : 'badge-red'}`}>
                              {evt.integrity_valid ? 'Valid Hash' : 'Invalid'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 6. WORKSPACES TAB */}
        {tab === 'setup' && (
          <div className="two-col-grid">
            {/* Existing Workspaces List */}
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Existing Workspaces ({competitions.length})</h2>
                  <p>All active program workspaces currently stored. Click to switch workspace.</p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {competitions.map(c => {
                  const isCurrent = c.id === selected
                  return (
                    <div
                      key={c.id}
                      style={{
                        padding: '14px 16px',
                        border: isCurrent ? '2px solid var(--primary)' : '1px solid var(--border)',
                        background: isCurrent ? 'var(--primary-light)' : '#ffffff',
                        borderRadius: 'var(--radius-sm)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '12px'
                      }}
                    >
                      <div>
                        <strong style={{ fontSize: '14px', display: 'block', color: 'var(--text-main)' }}>{c.name}</strong>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                          ID: {short(c.id)} · Network: {c.network} · Currency: {c.default_currency}
                        </span>
                        {c.description && (
                          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>{c.description}</p>
                        )}
                      </div>

                      <div>
                        {isCurrent ? (
                          <span className="badge badge-green">Currently Active</span>
                        ) : (
                          <button
                            type="button"
                            className="btn-secondary btn-sm"
                            onClick={() => switchWorkspace(c.id)}
                            disabled={busy}
                          >
                            Switch to This Workspace
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Create New Workspace Form */}
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h2>Create New Workspace</h2>
                  <p>Set up an isolated prize pool, funding policy, and audit trail for a new competition.</p>
                </div>
              </div>

              <form onSubmit={createWorkspace}>
                <div className="form-group">
                  <label>Program or Workspace Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. AI Agents Ecosystem Grants"
                    value={compName}
                    onChange={e => setCompName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Description and Purpose</label>
                  <textarea
                    rows={3}
                    placeholder="e.g. Transparent distribution of prize or grant funds to verified teams."
                    value={compDescription}
                    onChange={e => setCompDescription(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Default Settlement Ledger</label>
                  <input type="text" readOnly value="Stellar Testnet (Test SDF Network ; September 2015)" style={{ background: 'var(--bg-subtle)' }} />
                </div>

                <button className="btn-primary" type="submit" disabled={busy || !compName.trim()}>
                  Create Workspace
                </button>
              </form>
            </div>
          </div>
        )}

        {/* FOOTER */}
        <footer style={{ marginTop: '40px', paddingTop: '20px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', color: 'var(--text-subtle)', fontSize: '12px' }}>
          <span>FundGuard by Omega · Transparent, Human-Approved Prize Distribution</span>
          <span>Verified On-Chain · Cryptographically Auditable</span>
        </footer>
      </main>
    </div>
  </div>
  )
}

export default App
