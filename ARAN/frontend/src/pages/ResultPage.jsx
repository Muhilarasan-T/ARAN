/**
 * ARAN — Result Page
 * Shows the ML prediction result: probability gauge, risk level,
 * SHAP explanation, and mitigation panel.
 * Receives state from ProtectPage via React Router.
 */
import { useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { applyMitigation } from '../services/api'

const RISK_CONFIG = {
    LOW: { color: 'var(--green-safe)', bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.3)', icon: '🟢', label: 'LOW RISK', action: 'ALLOWED' },
    MEDIUM: { color: 'var(--amber-warn)', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)', icon: '🟡', label: 'MEDIUM RISK', action: 'RATE LIMIT' },
    HIGH: { color: 'var(--red-danger)', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)', icon: '🔴', label: 'HIGH RISK', action: 'BLOCK' },
}

const ACTION_LABELS = {
    ALLOW: { label: 'Allowed', color: 'var(--green-safe)', icon: '✅' },
    RATE_LIMIT: { label: 'Rate Limited', color: 'var(--amber-warn)', icon: '⏱️' },
    BLOCK: { label: 'Temporarily Blocked', color: 'var(--red-danger)', icon: '🚫' },
}

// Features to display with labels
const FEATURE_LABELS = {
    requests_per_minute: 'Requests / min',
    requests_per_second: 'Requests / sec',
    failed_request_ratio: 'Failure ratio',
    unique_endpoints: 'Unique endpoints',
    repeated_endpoint_ratio: 'Repeated endpoint',
    session_duration_sec: 'Session duration',
    login_attempts: 'Login attempts',
    login_failure_ratio: 'Login failures',
    endpoint_entropy: 'Endpoint entropy',
    request_interval_variance: 'Interval variance',
    status_4xx_count: '4xx count',
}

export default function ResultPage() {
    const { state } = useLocation()
    const navigate = useNavigate()
    const [mitigationApplied, setMitigationApplied] = useState(false)
    const [mitigationMsg, setMitigationMsg] = useState(null)
    const [applyingAction, setApplyingAction] = useState(null)

    // If user navigates directly without state, redirect
    if (!state?.result) {
        return (
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem' }}>
                <p style={{ color: 'var(--text-muted)' }}>No result data. Please run a simulation first.</p>
                <button className="btn btn-primary" onClick={() => navigate('/protect')}>← Go to Protection</button>
            </div>
        )
    }

    const result = state.result
    const prob = result.bot_probability ?? 0
    const risk = result.risk_level ?? 'LOW'
    const cfg = RISK_CONFIG[risk] ?? RISK_CONFIG.LOW
    const explanation = result.explanation ?? []
    const features = result.top_features ?? {}
    const trafficType = result.traffic_type

    const handleApply = async (action) => {
        setApplyingAction(action)
        try {
            const r = await applyMitigation({ sessionId: state.sessionId, action })
            setMitigationMsg(r.message)
            setMitigationApplied(true)
        } catch (e) {
            setMitigationMsg(`Error: ${e.message}`)
        } finally {
            setApplyingAction(null)
        }
    }

    // Progress bar color
    const probColor = prob >= 75 ? 'red' : prob >= 40 ? 'amber' : 'green'

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <header style={{ padding: '1.25rem 2rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                    onClick={() => navigate('/protect')}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem' }}
                >
                    ← New Test
                </button>
                <span className="gradient-text" style={{ fontWeight: 800, letterSpacing: '0.05em' }}>ARAN</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>RESULT</span>
            </header>

            <main className="container" style={{ flex: 1, paddingTop: '3rem', paddingBottom: '3rem' }}>

                {/* Main result hero */}
                <div className="card animate-fade-up" style={{
                    textAlign: 'center', marginBottom: '1.5rem',
                    background: cfg.bg, borderColor: cfg.border,
                    padding: '2.5rem 2rem',
                }}>
                    <div style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                        {trafficType === 'bot' ? '🔴 BOT DETECTED' : '🟢 LEGITIMATE REQUEST'}
                    </div>

                    <div className="prob-number" style={{ color: cfg.color }}>
                        {prob.toFixed(1)}%
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>Bot Probability</div>

                    <div style={{ maxWidth: 360, margin: '1.5rem auto 0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                            <span>Human</span><span>Bot</span>
                        </div>
                        <div className="progress-bar" style={{ height: 10 }}>
                            <div className={`progress-fill ${probColor}`} style={{ width: `${prob}%` }} />
                        </div>
                    </div>

                    <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                        <span className={`badge badge-${risk.toLowerCase()}`}>{cfg.icon} {cfg.label}</span>
                        <span className="badge badge-active">
                            {ACTION_LABELS[result.action]?.icon} {ACTION_LABELS[result.action]?.label}
                        </span>
                    </div>
                </div>

                {/* Explanation */}
                {explanation.length > 0 && (
                    <div className="card animate-fade-up" style={{ marginBottom: '1.5rem', animationDelay: '0.1s' }}>
                        <h3 style={{ marginBottom: '1rem' }}>
                            {risk !== 'LOW' ? '🔍 Why was this flagged as a bot?' : '✅ Why is this legitimate?'}
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                            {explanation.map((reason, i) => (
                                <div key={i} style={{
                                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                                    padding: '0.65rem 1rem', borderRadius: 'var(--radius-sm)',
                                    background: risk !== 'LOW' ? 'rgba(239,68,68,0.06)' : 'rgba(34,197,94,0.06)',
                                    border: `1px solid ${risk !== 'LOW' ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)'}`,
                                }}>
                                    <span style={{ color: risk !== 'LOW' ? 'var(--red-danger)' : 'var(--green-safe)', fontSize: '1.1rem' }}>
                                        {risk !== 'LOW' ? '⚠' : '✓'}
                                    </span>
                                    <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{reason}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Feature values */}
                {Object.keys(features).length > 0 && (
                    <div className="card animate-fade-up" style={{ marginBottom: '1.5rem', animationDelay: '0.2s' }}>
                        <h3 style={{ marginBottom: '1rem' }}>📊 Behavioral Feature Values</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.6rem' }}>
                            {Object.entries(features)
                                .filter(([k]) => FEATURE_LABELS[k])
                                .map(([key, val]) => (
                                    <div key={key} style={{
                                        padding: '0.6rem 0.8rem', background: 'rgba(79,156,249,0.04)',
                                        borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)'
                                    }}>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                                            {FEATURE_LABELS[key]}
                                        </div>
                                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--blue-primary)', fontWeight: 600 }}>
                                            {typeof val === 'number' ? val.toFixed(3) : val}
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                )}

                {/* Mitigation panel */}
                {(risk === 'MEDIUM' || risk === 'HIGH') && (
                    <div className="card animate-fade-up" style={{ marginBottom: '1.5rem', animationDelay: '0.3s' }}>
                        <h3 style={{ marginBottom: '0.5rem' }}>🛡️ Mitigation</h3>
                        <p style={{ fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                            ARAN recommends <strong style={{ color: cfg.color }}>{cfg.action}</strong> for this session.
                            Apply protection below.
                        </p>

                        {mitigationApplied ? (
                            <div style={{
                                background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)',
                                borderRadius: 'var(--radius-md)', padding: '1rem', color: 'var(--green-safe)', fontSize: '0.9rem'
                            }}>
                                ✅ {mitigationMsg}
                            </div>
                        ) : (
                            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                                <button
                                    id="apply-rate-limit-btn"
                                    className="btn btn-outline"
                                    disabled={!!applyingAction}
                                    onClick={() => handleApply('RATE_LIMIT')}
                                >
                                    {applyingAction === 'RATE_LIMIT' ? <><span className="spinner spinner-blue" /> Applying…</> : '⏱️ Rate Limit'}
                                </button>
                                <button
                                    id="apply-block-btn"
                                    className="btn btn-danger"
                                    disabled={!!applyingAction}
                                    onClick={() => handleApply('BLOCK')}
                                >
                                    {applyingAction === 'BLOCK' ? <><span className="spinner" /> Blocking…</> : '🚫 Block (10 min)'}
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* CTA row */}
                <div className="animate-fade-up" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', animationDelay: '0.4s' }}>
                    <button className="btn btn-primary" onClick={() => navigate('/protect')}>
                        Run Another Test
                    </button>
                    <button className="btn btn-outline" onClick={() => navigate('/')}>
                        ← Home
                    </button>
                </div>
            </main>
        </div>
    )
}
