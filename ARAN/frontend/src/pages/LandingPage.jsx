/**
 * ARAN — Landing Page
 * The first screen the user sees. Minimal, impactful.
 */
import { useNavigate } from 'react-router-dom'
import { useEffect, useRef } from 'react'

export default function LandingPage() {
    const navigate = useNavigate()
    const canvasRef = useRef(null)

    // Particle animation in background
    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')
        let animId
        const particles = []

        const resize = () => {
            canvas.width = window.innerWidth
            canvas.height = window.innerHeight
        }
        resize()
        window.addEventListener('resize', resize)

        for (let i = 0; i < 60; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                r: Math.random() * 1.5 + 0.5,
                alpha: Math.random() * 0.4 + 0.1,
            })
        }

        const draw = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height)
            particles.forEach(p => {
                p.x += p.vx; p.y += p.vy
                if (p.x < 0) p.x = canvas.width
                if (p.x > canvas.width) p.x = 0
                if (p.y < 0) p.y = canvas.height
                if (p.y > canvas.height) p.y = 0
                ctx.beginPath()
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
                ctx.fillStyle = `rgba(79, 156, 249, ${p.alpha})`
                ctx.fill()
            })
            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x
                    const dy = particles[i].y - particles[j].y
                    const dist = Math.sqrt(dx * dx + dy * dy)
                    if (dist < 120) {
                        ctx.beginPath()
                        ctx.moveTo(particles[i].x, particles[i].y)
                        ctx.lineTo(particles[j].x, particles[j].y)
                        ctx.strokeStyle = `rgba(79, 156, 249, ${0.08 * (1 - dist / 120)})`
                        ctx.lineWidth = 0.5
                        ctx.stroke()
                    }
                }
            }
            animId = requestAnimationFrame(draw)
        }
        draw()
        return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize) }
    }, [])

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
            {/* Particle canvas */}
            <canvas ref={canvasRef} style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }} />

            {/* Glow orbs */}
            <div style={{
                position: 'fixed', top: '20%', left: '10%', width: 400, height: 400,
                borderRadius: '50%', background: 'radial-gradient(circle, rgba(79,156,249,0.08) 0%, transparent 70%)',
                pointerEvents: 'none', zIndex: 0,
            }} />
            <div style={{
                position: 'fixed', bottom: '15%', right: '10%', width: 500, height: 500,
                borderRadius: '50%', background: 'radial-gradient(circle, rgba(167,139,250,0.06) 0%, transparent 70%)',
                pointerEvents: 'none', zIndex: 0,
            }} />

            {/* Header */}
            <header style={{ padding: '1.5rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 1 }}>
                <div style={{ fontWeight: 800, fontSize: '1.2rem', letterSpacing: '0.05em', color: 'var(--text-primary)' }}>
                    <span className="gradient-text">ARAN</span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className="pulse-dot blue" />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>ML ENGINE READY</span>
                </div>
            </header>

            {/* Hero */}
            <main style={{
                flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', padding: '4rem 1.5rem', position: 'relative', zIndex: 1, textAlign: 'center'
            }}>

                {/* Tagline chip */}
                <div className="animate-fade" style={{ animationDelay: '0.1s' }}>
                    <span style={{
                        background: 'rgba(79,156,249,0.12)', border: '1px solid rgba(79,156,249,0.3)',
                        borderRadius: '100px', padding: '0.35rem 1rem', fontSize: '0.78rem',
                        color: 'var(--blue-primary)', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600,
                    }}>
                        ML-Powered API Security
                    </span>
                </div>

                <h1 className="animate-fade-up gradient-text" style={{ marginTop: '1.5rem', animationDelay: '0.2s' }}>
                    ARAN
                </h1>

                <p className="animate-fade-up" style={{
                    fontSize: 'clamp(1rem, 2vw, 1.25rem)', maxWidth: 600,
                    marginTop: '1rem', color: 'var(--text-secondary)', animationDelay: '0.3s'
                }}>
                    Detect automated bot traffic in real time and protect your API
                    using machine learning — without blocking real users.
                </p>

                {/* Stats row */}
                <div className="animate-fade-up" style={{
                    display: 'flex', gap: '2rem', marginTop: '2.5rem', animationDelay: '0.4s',
                    flexWrap: 'wrap', justifyContent: 'center'
                }}>
                    {[
                        { value: 'XGBoost', label: 'ML Model' },
                        { value: '13', label: 'Behavioral Features' },
                        { value: 'SHAP', label: 'Explainability' },
                        { value: '<100ms', label: 'Inference Latency' },
                    ].map(stat => (
                        <div key={stat.label} style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--blue-primary)', fontFamily: 'var(--font-mono)' }}>
                                {stat.value}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.2rem' }}>
                                {stat.label}
                            </div>
                        </div>
                    ))}
                </div>

                {/* CTA */}
                <div className="animate-fade-up" style={{ marginTop: '3rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center', animationDelay: '0.5s' }}>
                    <button
                        id="try-demo-btn"
                        className="btn btn-primary btn-lg"
                        onClick={() => navigate('/demo')}
                    >
                        <span>🛡️</span> Try Demo
                    </button>
                    <a
                        href="https://github.com"
                        className="btn btn-outline btn-lg"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        View on GitHub
                    </a>
                </div>

                {/* Feature pills */}
                <div className="animate-fade-up" style={{ marginTop: '4rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center', animationDelay: '0.6s' }}>
                    {['Real-time Detection', 'XGBoost Classifier', 'SHAP Explainability', 'Automated Mitigation', 'WebSocket Events', 'Traffic Simulation'].map(f => (
                        <span key={f} style={{
                            background: 'var(--bg-card)', border: '1px solid var(--border)',
                            borderRadius: '100px', padding: '0.4rem 1rem', fontSize: '0.8rem', color: 'var(--text-secondary)'
                        }}>
                            {f}
                        </span>
                    ))}
                </div>

                {/* ML Pipeline visual */}
                <div className="animate-fade-up card" style={{
                    marginTop: '5rem', padding: '1.5rem 2rem', maxWidth: 700, width: '100%', animationDelay: '0.7s'
                }}>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
                        End-to-End ML Pipeline
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                        {['Traffic', '→', 'Feature Extraction', '→', 'XGBoost', '→', 'Bot Probability', '→', 'Mitigation'].map((step, i) => (
                            <span key={i} style={{
                                color: step === '→' ? 'var(--text-muted)' : 'var(--blue-primary)',
                                fontFamily: step === '→' ? 'inherit' : 'var(--font-mono)',
                                fontSize: '0.85rem', fontWeight: step === '→' ? 400 : 600,
                            }}>
                                {step}
                            </span>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    )
}
