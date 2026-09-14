"""
ARAN — Protection Routes

Handles start/stop protection and triggers traffic simulation + inference.
"""
import asyncio
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks

from models.schemas import SimulationRequest, PredictionResult
from services.inference import predict
from services.feature_extractor import extract_features
from services.mitigation_engine import apply_mitigation
from services.explainer import build_explanation
from websocket.manager import ws_manager
from simulation.normal_user import simulate_normal_user
from simulation.bot_attack import simulate_bot_attack
from config import get_risk_level, get_recommended_action

router = APIRouter()
logger = logging.getLogger("aran.protection")


@router.get("/status")
async def protection_status():
    return {"protection": "active", "model": "xgboost_v1"}


@router.post("/simulate")
async def start_simulation(req: SimulationRequest, background_tasks: BackgroundTasks):
    """
    Kicks off a traffic simulation in the background.
    The simulation sends real HTTP requests to /demo/* endpoints,
    collects session stats, then runs ML inference and broadcasts results via WebSocket.
    """
    background_tasks.add_task(_run_simulation, req)
    return {"message": "Simulation started", "session_id": req.session_id}


async def _run_simulation(req: SimulationRequest):
    """Background task: simulate → extract → predict → mitigate → broadcast."""
    session_id = req.session_id
    logger.info(f"[{session_id}] Starting {req.traffic_type} simulation ({req.request_count} requests)")

    try:
        # 1. Broadcast simulation start
        await ws_manager.broadcast({
            "event": "simulation_start",
            "session_id": session_id,
            "traffic_type": req.traffic_type,
            "request_count": req.request_count,
        })

        # 2. Run appropriate simulator
        if req.traffic_type == "bot":
            session_stats = await simulate_bot_attack(session_id, req.request_count)
        else:
            session_stats = await simulate_normal_user(session_id, req.request_count)

        # 3. Broadcast raw stats
        await ws_manager.broadcast({
            "event": "traffic_captured",
            "session_id": session_id,
            **session_stats,
        })

        # 4. Extract feature vector
        features = extract_features(session_stats)

        # 5. ML inference
        bot_probability, raw_features = predict(features)

        # 6. Risk classification
        risk_level = get_risk_level(bot_probability)
        action = get_recommended_action(risk_level)

        # 7. Explanation
        explanation = build_explanation(raw_features, bot_probability)

        # 8. Mitigation
        mitigation_result = apply_mitigation(session_id, action)

        # 9. Broadcast final result
        await ws_manager.broadcast({
            "event": "prediction_complete",
            "session_id": session_id,
            "traffic_type": req.traffic_type,
            "bot_probability": round(bot_probability * 100, 1),
            "risk_level": risk_level,
            "action": action,
            "explanation": explanation,
            "top_features": raw_features,
            "mitigation": mitigation_result,
        })

        logger.info(f"[{session_id}] Result: {risk_level} ({bot_probability:.1%}) → {action}")

    except Exception as e:
        logger.error(f"[{session_id}] Simulation error: {e}")
        await ws_manager.broadcast({
            "event": "error",
            "session_id": session_id,
            "message": str(e),
        })
