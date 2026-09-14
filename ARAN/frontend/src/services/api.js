/**
 * ARAN API Service
 * Centralized HTTP client for all backend interactions.
 */

const BASE_URL = '/protection'  // proxied to http://localhost:8000

export async function startSimulation({ sessionId, trafficType, requestCount = 50 }) {
    const res = await fetch(`${BASE_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            traffic_type: trafficType,
            request_count: requestCount,
        }),
    })
    if (!res.ok) throw new Error(`Simulation start failed: ${res.status}`)
    return res.json()
}

export async function applyMitigation({ sessionId, action }) {
    const res = await fetch('/mitigation/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, action }),
    })
    if (!res.ok) throw new Error(`Mitigation failed: ${res.status}`)
    return res.json()
}

export async function getHealth() {
    const res = await fetch('/health')
    return res.json()
}

/** Generate a short unique session ID */
export function newSessionId() {
    return `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`
}
