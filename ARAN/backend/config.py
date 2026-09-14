"""
ARAN — Configuration
Loads settings from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "info"

    # Frontend origin for CORS
    frontend_origin: str = "http://localhost:5173"

    # ML model paths (relative to backend/ working dir)
    model_path: str = "../models/xgboost_model.pkl"
    preprocessor_path: str = "../models/preprocessor.pkl"

    # Risk thresholds
    risk_low_max: float = 0.40
    risk_medium_max: float = 0.75

    # Mitigation
    block_duration_seconds: int = 600
    rate_limit_requests_per_minute: int = 30

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


settings = Settings()


def get_risk_level(probability: float) -> str:
    """Convert a bot probability (0–1) to a risk level string."""
    if probability < settings.risk_low_max:
        return "LOW"
    elif probability < settings.risk_medium_max:
        return "MEDIUM"
    else:
        return "HIGH"


def get_recommended_action(risk_level: str) -> str:
    """Map risk level to the recommended mitigation action."""
    return {
        "LOW": "ALLOW",
        "MEDIUM": "RATE_LIMIT",
        "HIGH": "BLOCK",
    }.get(risk_level, "ALLOW")
