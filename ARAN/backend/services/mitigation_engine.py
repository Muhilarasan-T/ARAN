"""
ARAN — Mitigation Engine (In-Memory)

Tracks blocked and rate-limited sessions in server memory.
For V1, this is sufficient for a demo environment.

In a production system, this state would live in Redis so multiple
backend workers could share it.

Interview concept: Rate limiting and blocking
--------------------------------------------
Rate limiting restricts the number of requests per time window.
Blocking denies access entirely for a time period.
For this demo, both are implemented as simple in-memory dicts
with timestamps — lightweight, zero-dependency.
"""
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from config import settings
from models.schemas import MitigationAction, MitigationResult

logger = logging.getLogger("aran.mitigation")

# In-memory state stores
# { session_id: expires_at_unix_timestamp }
_blocked_sessions: dict = {}
_rate_limited_sessions: dict = {}

# Counters for dashboard
_total_blocked = 0
_total_rate_limited = 0


def apply_mitigation(session_id: str, action: str) -> dict:
    """
    Apply the mitigation action to a session.

    Args:
        session_id: unique session identifier
        action: 'ALLOW', 'RATE_LIMIT', or 'BLOCK'

    Returns:
        dict with action result details
    """
    global _total_blocked, _total_rate_limited

    now = time.time()
    expires_at = now + settings.block_duration_seconds

    if action == MitigationAction.BLOCK:
        _blocked_sessions[session_id] = expires_at
        _total_blocked += 1
        logger.warning(f"[BLOCKED] session={session_id} expires_in={settings.block_duration_seconds}s")
        return {
            "session_id": session_id,
            "action": "BLOCK",
            "message": f"Session blocked for {settings.block_duration_seconds // 60} minutes.",
            "block_expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        }

    elif action == MitigationAction.RATE_LIMIT:
        _rate_limited_sessions[session_id] = expires_at
        _total_rate_limited += 1
        logger.warning(f"[RATE_LIMITED] session={session_id}")
        return {
            "session_id": session_id,
            "action": "RATE_LIMIT",
            "message": f"Rate limited to {settings.rate_limit_requests_per_minute} req/min.",
            "block_expires_at": None,
        }

    else:  # ALLOW
        logger.info(f"[ALLOWED] session={session_id}")
        return {
            "session_id": session_id,
            "action": "ALLOW",
            "message": "Request allowed. No threat detected.",
            "block_expires_at": None,
        }


def is_blocked(session_id: str) -> bool:
    """Returns True if the session is currently blocked."""
    _cleanup_expired()
    return session_id in _blocked_sessions


def is_rate_limited(session_id: str) -> bool:
    """Returns True if the session is currently rate limited."""
    _cleanup_expired()
    return session_id in _rate_limited_sessions


def get_session_status(session_id: str) -> dict:
    """Returns current mitigation status for a session."""
    _cleanup_expired()
    if session_id in _blocked_sessions:
        return {"status": "BLOCKED", "expires_at": _blocked_sessions[session_id]}
    elif session_id in _rate_limited_sessions:
        return {"status": "RATE_LIMITED", "expires_at": _rate_limited_sessions[session_id]}
    return {"status": "CLEAN"}


def unblock_session(session_id: str) -> dict:
    """Manually remove a session from block/rate-limit lists."""
    removed = False
    if session_id in _blocked_sessions:
        del _blocked_sessions[session_id]
        removed = True
    if session_id in _rate_limited_sessions:
        del _rate_limited_sessions[session_id]
        removed = True
    return {"session_id": session_id, "unblocked": removed}


def get_global_stats() -> dict:
    """Return aggregate mitigation statistics."""
    _cleanup_expired()
    return {
        "currently_blocked": len(_blocked_sessions),
        "currently_rate_limited": len(_rate_limited_sessions),
        "total_blocked_all_time": _total_blocked,
        "total_rate_limited_all_time": _total_rate_limited,
    }


def _cleanup_expired():
    """Remove expired entries from in-memory stores."""
    now = time.time()
    expired_blocks = [sid for sid, exp in _blocked_sessions.items() if exp < now]
    expired_rl = [sid for sid, exp in _rate_limited_sessions.items() if exp < now]
    for sid in expired_blocks:
        del _blocked_sessions[sid]
    for sid in expired_rl:
        del _rate_limited_sessions[sid]
