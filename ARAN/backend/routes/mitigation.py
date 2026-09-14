"""
ARAN — Mitigation Routes

Allows manual mitigation actions (the user can click Rate Limit / Block).
"""
from fastapi import APIRouter
from models.schemas import MitigationRequest, MitigationResult
from services.mitigation_engine import apply_mitigation, get_session_status

router = APIRouter()


@router.post("/apply", response_model=MitigationResult)
async def apply_action(req: MitigationRequest):
    """Apply a mitigation action to a session."""
    result = apply_mitigation(req.session_id, req.action)
    return result


@router.get("/status/{session_id}")
async def session_status(session_id: str):
    """Get current mitigation status for a session."""
    return get_session_status(session_id)


@router.delete("/unblock/{session_id}")
async def unblock_session(session_id: str):
    """Manually unblock a session."""
    from services.mitigation_engine import unblock_session as _unblock
    return _unblock(session_id)
