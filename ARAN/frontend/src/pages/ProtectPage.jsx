/**
 * ARAN — Protect Page
 * The main protection screen. User chooses Normal User or Bot Attack.
 * Shows real-time WebSocket events and navigates to Result on completion.
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import { startSimulation, newSessionId } from '../services/api'

const REQUEST_COUNTS = { human: 20, bot: 80 }

export default function ProtectPage() {
    const navigate = useNavigate()
    const { isConnected, events, lastEvent, clearEvents } = useWebSocket()
    const [status, setStatus] = useState('idle')  // idle | running | done
    const [sessionId] = useState(newSessionId)
    const [selectedType, setSelectedType] = useState(null)
    const [error, setError] = useState(null)

    // When prediction arrives, navigate to result page
    useEffect(() => {
        if (lastEvent?.event === 'prediction_complete') {
            setTimeout(() => navigate('/result', { state: { result: lastEvent, sessionId } }), 800)
        }
        if (lastEvent?.event === 'error') {
            setError(lastEvent.message)
            setStatus('idle')
        }
    }, [lastEvent, navigate, sessionId])

    const runSimulation = useCallback(async (trafficType) => {
        setSelectedType(trafficType)
        setStatus('running')
        setError(null)
        clearEvents()
        try {
            await startSimulation({
                sessionId,
                trafficType,
                requestCount: REQUEST_COUNTS[trafficType],
            })
        } catch (e) {
            setError(e.message)
            setStatus('idle')
        }
    }, [sessionId, clearEvents])

    // Map event type to log class
    const eventClass = (ev) => {
        if (!ev?.event) return ''
        if (ev.event === 'prediction_complete') return ev.risk_level === 'LOW' ? 'success' : 'danger'
        if (ev.event === 'simulation_start') return 'info'
        if (ev.event === 'traffic_captured') return 'warning'
        if (ev.event === 'error') return 'danger'
        return ''
    }

    const eventLabel = (ev) => {
        switch (ev?.event) {
            case 'simulation_start': return `[SIM_START] ${ev.traffic_type?.toUpperCase()} — ${ev.request_count} requests`
            case 'traffic_captured': return `[TRAFFIC] ${ev.total_requests} requests in ${ev.session_duration_sec?.toFixed(1)}s`
            case 'prediction_complete': return `[RESULT] Bot: ${ev.bot_probability}% | Risk: ${ev.risk_level} | Action: ${ev.action}`
            case 'error': return `[ERROR] ${ev.message}`
            default: return JSON.stringify(ev)
        }
    }

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <header style={{ padding: '1.25rem 2rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                    onClick={() => navigate('/demo')}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem' }}
                >
                    ← Demo API
                </button>
                <span className="gradient-text" style={{ fontWeight: 800, letterSpacing: '0.05em' }}>ARAN</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`pulse-dot ${isConnected ? 'blue' : 'red'}`} />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {isConnected ? 'WS CONNECTED' : 'CONNECTING…'}
                    </span>
                </div>
            </header>

            <main className="container" style={{ flex: 1, paddingTop: '3rem', paddingBottom: '3rem' }}>

                {/* Status banner */}
                <div className="card animate-fade-up" style={{
                    textAlign: 'center', marginBottom: '2.5rem',
                    background: status === 'running' ? 'rgba(79,156,249,0.08)' : undefined,
                    borderColor: status === 'running' ? 'var(--border-bright)' : undefined,
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <span className={`pulse-dot ${status === 'running' ? 'blue' : 'green'}`} />
                        <h2>{status === 'running' ? 'Analyzing Traffic…' : 'ARAN is Protecting Your API'}</h2>
                    </div>
                    <p style={{ maxWidth: 480, margin: '0 auto', fontSize: '0.95rem' }}>
                        {status === 'running'
                            ? `Sending ${selectedType === 'bot' ? 'bot attack' : 'normal user'} traffic to the Demo API and running ML inference…`
                            : 'Incoming requests are monitored and analyzed in real time using XGBoost.'
                        }
                    </p>
                    <div style={{ marginTop: '1rem' }}>
                        <span className="badge badge-active">🟢 ACTIVE</span>
                    </div>
                </div>

                {/* Traffic buttons */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '2rem' }}>
                    {/* Normal User */}
                    <div className="card animate-fade-up" style={{
                        animationDelay: '0.1s', cursor: status === 'running' ? 'not-allowed' : 'pointer',
                        opacity: status === 'running' && selectedType !== 'human' ? 0.5 : 1,
                        borderColor: selectedType === 'human' && status === 'running' ? 'var(--green-safe)' : undefined,
                        textAlign: 'center',
                    }}>
                        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🟢</div>
                        <h3>Normal User</h3>
                        <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', marginBottom: '1.25rem' }}>
                            Simulates realistic human browsing — diverse endpoints, natural intervals, low failure rate.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1.25rem', textAlign: 'left' }}>
                            {['5–20 requests/min', 'Varied endpoint access', '~5% failure rate', 'High interval variance'].map(f => (
                                <span key={f} style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--green-safe)' }}>✓</span> {f}
                                </span>
                            ))}
                        </div>
                        <button
                            id="normal-user-btn"
                            className="btn btn-success w-full"
                            disabled={status === 'running'}
                            onClick={() => runSimulation('human')}
                        >
                            {status === 'running' && selectedType === 'human' ? <><span className="spinner" /> Running…</> : 'Simulate Normal User'}
                        </button>
                    </div>

                    {/* Bot Attack */}
                    <div className="card animate-fade-up" style={{
                        animationDelay: '0.2s', cursor: status === 'running' ? 'not-allowed' : 'pointer',
                        opacity: status === 'running' && selectedType !== 'bot' ? 0.5 : 1,
                        borderColor: selectedType === 'bot' && status === 'running' ? 'var(--red-danger)' : undefined,
                        textAlign: 'center',
                    }}>
                        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🔴</div>
                        <h3>Bot Attack</h3>
                        <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', marginBottom: '1.25rem' }}>
                            Simulates automated bot behavior — high rate, repeated endpoints, credential stuffing.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1.25rem', textAlign: 'left' }}>
                            {['200–500 requests/min', 'Concentrated endpoints', '40–70% failure rate', 'Near-zero interval variance'].map(f => (
                                <span key={f} style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--red-danger)' }}>⚠</span> {f}
                                </span>
                            ))}
                        </div>
                        <button
                            id="bot-attack-btn"
                            className="btn btn-danger w-full"
                            disabled={status === 'running'}
                            onClick={() => runSimulation('bot')}
                        >
                            {status === 'running' && selectedType === 'bot' ? <><span className="spinner" /> Running…</> : 'Simulate Bot Attack'}
                        </button>
                    </div>
                </div>

                {/* Error display */}
                {error && (
                    <div className="animate-fade" style={{
                        background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                        borderRadius: 'var(--radius-md)', padding: '1rem 1.25rem', marginBottom: '1.5rem',
                        color: 'var(--red-danger)', fontSize: '0.9rem'
                    }}>
                        ⚠ {error}
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.3rem' }}>
                            Make sure the ARAN backend is running on port 8000.
                        </span>
                    </div>
                )}

                {/* Live event log */}
                <div className="animate-fade-up" style={{ animationDelay: '0.3s' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                            Live Event Stream
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {events.length} events
                        </span>
                    </div>
                    <div className="event-log">
                        {events.length === 0 ? (
                            <div style={{ color: 'var(--text-muted)', padding: '0.5rem 0' }}>
                                {'>'} Waiting for traffic simulation…
                            </div>
                        ) : (
                            events.map((ev, i) => (
                                <div key={i} className={`event-log-entry ${eventClass(ev)}`}>
                                    <span className="ts">[{ev._receivedAt?.slice(11, 19)}]</span>
                                    {eventLabel(ev)}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </main>
        </div>
    )
}
