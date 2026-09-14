/**
 * useWebSocket — custom hook for WebSocket connection to ARAN backend
 *
 * Maintains a single persistent WebSocket connection.
 * Broadcasts structured events from the backend to the component using the hook.
 *
 * Usage:
 *   const { events, lastEvent, isConnected } = useWebSocket()
 */
import { useState, useEffect, useRef, useCallback } from 'react'

const WS_URL = 'ws://localhost:8000/ws'
const RECONNECT_DELAY_MS = 3000

export function useWebSocket() {
    const [isConnected, setIsConnected] = useState(false)
    const [events, setEvents] = useState([])
    const [lastEvent, setLastEvent] = useState(null)
    const ws = useRef(null)
    const reconnectTimer = useRef(null)

    const connect = useCallback(() => {
        if (ws.current?.readyState === WebSocket.OPEN) return

        ws.current = new WebSocket(WS_URL)

        ws.current.onopen = () => {
            setIsConnected(true)
            clearTimeout(reconnectTimer.current)
        }

        ws.current.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data)
                const event = { ...data, _receivedAt: new Date().toISOString() }
                setLastEvent(event)
                setEvents(prev => [event, ...prev].slice(0, 100)) // keep last 100 events
            } catch {
                console.warn('ARAN WS: could not parse message', e.data)
            }
        }

        ws.current.onclose = () => {
            setIsConnected(false)
            // Auto-reconnect
            reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
        }

        ws.current.onerror = () => {
            ws.current?.close()
        }
    }, [])

    useEffect(() => {
        connect()
        return () => {
            clearTimeout(reconnectTimer.current)
            ws.current?.close()
        }
    }, [connect])

    const clearEvents = useCallback(() => {
        setEvents([])
        setLastEvent(null)
    }, [])

    return { isConnected, events, lastEvent, clearEvents }
}
