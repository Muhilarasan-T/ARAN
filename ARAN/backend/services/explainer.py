"""
ARAN — Explainer Service

Converts raw feature values and bot probability into plain-English
explanations a non-technical user can understand.

Uses SHAP TreeExplainer when the model is loaded.
Falls back to rule-based explanation in demo mode.

Interview concept: Model explainability / SHAP
----------------------------------------------
SHAP (SHapley Additive exPlanations) assigns each feature a "contribution"
value for a specific prediction. Positive SHAP = pushed prediction toward bot.
Negative SHAP = pushed prediction toward human.

For each prediction, we pick the top 3 features with the highest positive
SHAP values and translate them into plain sentences for the UI.

This is important because: regulators and users want to know WHY the model
classified a request as a bot, not just that it did.
"""
import logging
import numpy as np
import pandas as pd
from typing import List

logger = logging.getLogger("aran.explainer")

# Lazy-load SHAP to avoid startup delay
_shap_explainer = None

# Human-readable descriptions for each feature
FEATURE_DESCRIPTIONS = {
    "requests_per_minute": "Unusually high request frequency",
    "requests_per_second": "Extreme burst rate of requests",
    "failed_request_ratio": "High ratio of failed requests",
    "unique_endpoints": "Very few distinct endpoints accessed",
    "repeated_endpoint_ratio": "Highly repetitive endpoint access",
    "avg_response_time_ms": "Abnormal response time pattern",
    "session_duration_sec": "Very short session duration",
    "avg_payload_size_bytes": "Atypical payload size",
    "login_attempts": "Excessive login attempts",
    "login_failure_ratio": "High login failure ratio",
    "endpoint_entropy": "Very low endpoint diversity (bot-like)",
    "request_interval_variance": "Near-zero variance in request timing",
    "status_4xx_count": "High count of 4xx error responses",
}

# Thresholds above which a feature is "suspicious" (used in rule-based mode)
SUSPICIOUS_THRESHOLDS = {
    "requests_per_minute": 80,
    "requests_per_second": 2.0,
    "failed_request_ratio": 0.25,
    "repeated_endpoint_ratio": 0.65,
    "login_failure_ratio": 0.40,
    "request_interval_variance": 0.05,  # LOW variance = suspicious
    "status_4xx_count": 10,
    "login_attempts": 15,
}


def build_explanation(features: dict, bot_probability: float) -> List[str]:
    """
    Return a list of plain-English reasons why this request was flagged.

    Args:
        features: feature dict from extract_features()
        bot_probability: the model's predicted bot probability

    Returns:
        List of 2–4 human-readable reason strings
    """
    from services.inference import _model, _preprocessor, FEATURE_COLUMNS

    if _model is not None and _preprocessor is not None:
        try:
            return _shap_explanation(features, FEATURE_COLUMNS, _model, _preprocessor)
        except Exception as e:
            logger.warning(f"SHAP failed, using rule-based fallback: {e}")

    return _rule_based_explanation(features, bot_probability)


def _shap_explanation(features: dict, columns: list, model, preprocessor) -> List[str]:
    """Use SHAP TreeExplainer to find top contributing features."""
    global _shap_explainer
    import shap

    if _shap_explainer is None:
        _shap_explainer = shap.TreeExplainer(model)

    df = pd.DataFrame([features])[columns]
    X_scaled = preprocessor.transform(df)
    shap_vals = _shap_explainer.shap_values(X_scaled)

    # shap_vals shape: (1, n_features) for binary XGBoost
    if isinstance(shap_vals, list):
        # Old SHAP API: shap_vals[1] = contributions toward class 1 (bot)
        contributions = shap_vals[1][0]
    else:
        contributions = shap_vals[0]

    # Sort by absolute contribution, descending
    sorted_features = sorted(
        zip(columns, contributions),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    reasons = []
    for feat, contrib in sorted_features[:4]:
        if contrib > 0.05:  # Only include features pushing toward bot
            desc = FEATURE_DESCRIPTIONS.get(feat, feat)
            reasons.append(desc)
        if len(reasons) >= 3:
            break

    return reasons if reasons else ["Unusual overall traffic pattern detected"]


def _rule_based_explanation(features: dict, bot_probability: float) -> List[str]:
    """
    Simple threshold-based explanation when model is not loaded.
    Used in demo mode / before training is complete.
    """
    reasons = []

    if features.get("requests_per_minute", 0) > SUSPICIOUS_THRESHOLDS["requests_per_minute"]:
        reasons.append(FEATURE_DESCRIPTIONS["requests_per_minute"])

    if features.get("failed_request_ratio", 0) > SUSPICIOUS_THRESHOLDS["failed_request_ratio"]:
        reasons.append(FEATURE_DESCRIPTIONS["failed_request_ratio"])

    if features.get("repeated_endpoint_ratio", 0) > SUSPICIOUS_THRESHOLDS["repeated_endpoint_ratio"]:
        reasons.append(FEATURE_DESCRIPTIONS["repeated_endpoint_ratio"])

    if features.get("request_interval_variance", 1.0) < SUSPICIOUS_THRESHOLDS["request_interval_variance"]:
        reasons.append(FEATURE_DESCRIPTIONS["request_interval_variance"])

    if features.get("login_failure_ratio", 0) > SUSPICIOUS_THRESHOLDS["login_failure_ratio"]:
        reasons.append(FEATURE_DESCRIPTIONS["login_failure_ratio"])

    if features.get("login_attempts", 0) > SUSPICIOUS_THRESHOLDS["login_attempts"]:
        reasons.append(FEATURE_DESCRIPTIONS["login_attempts"])

    if not reasons:
        if bot_probability > 0.75:
            reasons = ["Unusual overall traffic pattern detected"]
        else:
            reasons = ["Traffic pattern slightly above normal baseline"]

    return reasons[:3]
