/**
 * ARAN — Demo API Page
 * Shows the Demo Shopping API card and lets the user start protection.
 */
import { useNavigate } from 'react-router-dom'

const ENDPOINTS = [
    { method: 'GET', path: '/demo/products', desc: 'Product catalog' },
    { method: 'GET', path: '/demo/search', desc: 'Product search' },
    { method: 'GET', path: '/demo/product/{id}', desc: 'Single product' },
    { method: 'POST', path: '/demo/login', desc: 'User login' },
    { method: 'GET', path: '/demo/cart', desc: 'Shopping cart' },
    { method: 'POST', path: '/demo/checkout', desc: 'Checkout' },
]

const METHOD_COLORS = { GET: '#22c55e', POST: '#4f9cf9' }

export default function DemoPage() {
    const navigate = useNavigate()

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* Nav */}
            <header style={{ padding: '1.25rem 2rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                    onClick={() => navigate('/')}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                >
                    ← Back
                </button>
                <span className="gradient-text" style={{ fontWeight: 800, letterSpacing: '0.05em' }}>ARAN</span>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className="pulse-dot green" />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>DEMO API ONLINE</span>
                </div>
            </header>

            <main className="container" style={{ flex: 1, paddingTop: '4rem', paddingBottom: '4rem' }}>
                <div className="animate-fade-up text-center" style={{ marginBottom: '3rem' }}>
                    <span style={{
                        background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.3)',
                        borderRadius: '100px', padding: '0.35rem 1rem', fontSize: '0.78rem',
                        color: 'var(--green-safe)', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600
                    }}>
                        Demo API
                    </span>
                    <h2 style={{ marginTop: '1rem' }}>Shopping API</h2>
                    <p style={{ marginTop: '0.5rem', maxWidth: 480, margin: '0.75rem auto 0' }}>
                        This API represents a typical e-commerce backend. ARAN will monitor all incoming
                        traffic and detect bot attacks in real time.
                    </p>
                </div>

                {/* API Status card */}
                <div className="card animate-fade-up" style={{ marginBottom: '1.5rem', animationDelay: '0.1s' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                        <div>
                            <h3>API Protection Status</h3>
                            <p style={{ marginTop: '0.25rem', fontSize: '0.9rem' }}>
                                Start ARAN protection to begin monitoring incoming requests.
                            </p>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <span className="badge badge-active">🟢 Protection Ready</span>
                        </div>
                    </div>
                </div>

                {/* API Endpoints */}
                <div className="card animate-fade-up" style={{ marginBottom: '2rem', animationDelay: '0.2s' }}>
                    <h3 style={{ marginBottom: '1.25rem' }}>API Endpoints</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                        {ENDPOINTS.map(ep => (
                            <div key={ep.path} style={{
                                display: 'flex', alignItems: 'center', gap: '1rem',
                                padding: '0.65rem 1rem', background: 'rgba(79,156,249,0.04)',
                                borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)'
                            }}>
                                <span style={{
                                    fontFamily: 'var(--font-mono)', fontSize: '0.72rem', fontWeight: 700,
                                    color: METHOD_COLORS[ep.method], background: `${METHOD_COLORS[ep.method]}1a`,
                                    padding: '0.2rem 0.5rem', borderRadius: '4px', minWidth: 42, textAlign: 'center'
                                }}>
                                    {ep.method}
                                </span>
                                <code style={{ flex: 1, fontSize: '0.85rem', color: 'var(--text-code)' }}>{ep.path}</code>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{ep.desc}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Start Protection CTA */}
                <div className="animate-fade-up" style={{ textAlign: 'center', animationDelay: '0.3s' }}>
                    <button
                        id="start-protection-btn"
                        className="btn btn-primary btn-lg"
                        onClick={() => navigate('/protect')}
                    >
                        <span>🛡️</span> Start Protection
                    </button>
                    <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Protection runs locally — no real API keys required.
                    </p>
                </div>
            </main>
        </div>
    )
}
