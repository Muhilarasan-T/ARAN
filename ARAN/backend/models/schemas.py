"""
ARAN — Pydantic Schemas
Request / response models shared across routes.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MitigationAction(str, Enum):
    ALLOW = "ALLOW"
    RATE_LIMIT = "RATE_LIMIT"
    BLOCK = "BLOCK"


class SimulationRequest(BaseModel):
    session_id: str = Field(..., description="Unique ID for this simulation session")
    traffic_type: str = Field(..., description="'human' or 'bot'")
    request_count: int = Field(default=30, ge=1, le=1000)


class PredictionResult(BaseModel):
    session_id: str
    bot_probability: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    action: MitigationAction
    explanation: List[str]
    top_features: dict


class MitigationRequest(BaseModel):
    session_id: str
    action: MitigationAction


class MitigationResult(BaseModel):
    session_id: str
    action: MitigationAction
    message: str
    block_expires_at: Optional[str] = None


class SessionFeatures(BaseModel):
    """Feature vector extracted from a live session window."""
    requests_per_minute: float
    requests_per_second: float
    failed_request_ratio: float
    unique_endpoints: int
    repeated_endpoint_ratio: float
    avg_response_time_ms: float
    session_duration_sec: float
    avg_payload_size_bytes: float
    login_attempts: int
    login_failure_ratio: float
    endpoint_entropy: float
    request_interval_variance: float
    status_4xx_count: int
