"""
ARAN — ML Inference Service

Loads the trained XGBoost model and preprocessor from disk at startup.
Provides a predict() function called by routes — model is NEVER retrained
per request.

Interview concept: Model serialization + real-time inference
-------------------------------------------------------------
We train the model ONCE offline (in ml/train.py), then save it to disk
using joblib. At startup, the FastAPI app loads it into memory.
Every incoming request uses the already-loaded model — no retraining.
This is how production ML systems work: train → serialize → serve.
"""
import logging
import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple

from config import settings

logger = logging.getLogger("aran.inference")

# Module-level model and preprocessor — loaded once at startup
_model = None
_preprocessor = None

# Feature column order must match what the model was trained on
FEATURE_COLUMNS = [
    "requests_per_minute",
    "requests_per_second",
    "failed_request_ratio",
    "unique_endpoints",
    "repeated_endpoint_ratio",
    "avg_response_time_ms",
    "session_duration_sec",
    "avg_payload_size_bytes",
    "login_attempts",
    "login_failure_ratio",
    "endpoint_entropy",
    "request_interval_variance",
    "status_4xx_count",
]


def load_model():
    """
    Called once at application startup via FastAPI lifespan.
    Loads model and preprocessor from the paths specified in config.
    If model files don't exist yet (before Phase 5), runs in demo mode.
    """
    global _model, _preprocessor

    model_path = os.path.abspath(settings.model_path)
    preprocessor_path = os.path.abspath(settings.preprocessor_path)

    if os.path.exists(model_path) and os.path.exists(preprocessor_path):
        _model = joblib.load(model_path)
        _preprocessor = joblib.load(preprocessor_path)
        logger.info(f"Model loaded from {model_path}")
        logger.info(f"Preprocessor loaded from {preprocessor_path}")
    else:
        logger.warning(
            "Model files not found. Running in DEMO mode with rule-based scoring. "
            "Run ml/train.py to generate real models."
        )


def predict(features: dict) -> Tuple[float, dict]:
    """
    Run inference on an extracted feature dict.

    Returns:
        bot_probability: float between 0 and 1
        feature_dict: the feature values used for inference (for explanation)

    Interview concept: predict_proba vs predict
    -------------------------------------------
    XGBoost predict() returns a class label (0 or 1).
    predict_proba() returns probabilities [P(human), P(bot)].
    We use predict_proba()[:, 1] to get the bot probability, which is much
    more useful than just a binary decision — it lets us apply risk thresholds
    and show confidence to the user.
    """
    feature_df = pd.DataFrame([features])[FEATURE_COLUMNS]

    if _model is not None and _preprocessor is not None:
        # Real model path
        X_scaled = _preprocessor.transform(feature_df)
        prob = float(_model.predict_proba(X_scaled)[0][1])
    else:
        # Demo mode: rule-based scoring when model not yet trained
        prob = _demo_score(features)

    return prob, features


def _demo_score(features: dict) -> float:
    """
    Rule-based bot probability for demo mode (before ML model is trained).
    Not used in production — replaced by XGBoost predict_proba.
    """
    score = 0.0
    if features.get("requests_per_minute", 0) > 100:
        score += 0.4
    if features.get("failed_request_ratio", 0) > 0.3:
        score += 0.25
    if features.get("repeated_endpoint_ratio", 0) > 0.7:
        score += 0.2
    if features.get("request_interval_variance", 1) < 0.1:
        score += 0.15
    return min(score, 0.99)
