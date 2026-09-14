"""
ARAN — Feature Extractor

Converts raw session statistics (collected by the simulator) into the
exact feature vector expected by the trained XGBoost model.

Interview concept: Feature engineering for real-time inference
--------------------------------------------------------------
During training, features were computed from the synthetic dataset rows.
In production, we must compute the EXACT SAME features from live session data.
This file is the bridge — it applies the same logic the training dataset used,
ensuring train/serve consistency.

If you change the training features, you must update this file too.
"""
import math
import logging

logger = logging.getLogger("aran.feature_extractor")


def extract_features(session_stats: dict) -> dict:
    """
    Convert raw session stats from the simulator into a model-ready feature dict.

    Args:
        session_stats: dict produced by simulate_normal_user() or simulate_bot_attack()
                       containing raw request logs and aggregated counts.

    Returns:
        dict with exactly the 13 features the model was trained on.
    """
    total_requests = max(session_stats.get("total_requests", 1), 1)
    session_duration = max(session_stats.get("session_duration_sec", 1), 0.1)
    failed_requests = session_stats.get("failed_requests", 0)
    login_attempts = session_stats.get("login_attempts", 0)
    login_failures = session_stats.get("login_failures", 0)
    endpoint_counts = session_stats.get("endpoint_counts", {})
    response_times = session_stats.get("response_times_ms", [100])
    request_intervals = session_stats.get("request_intervals_sec", [1.0])
    payload_sizes = session_stats.get("payload_sizes_bytes", [512])
    status_4xx_count = session_stats.get("status_4xx_count", 0)

    # --- Core rate features ---
    requests_per_minute = (total_requests / session_duration) * 60
    requests_per_second = total_requests / session_duration

    # --- Failure behavior ---
    failed_request_ratio = failed_requests / total_requests

    # --- Endpoint diversity ---
    unique_endpoints = len(endpoint_counts)
    most_repeated = max(endpoint_counts.values(), default=0)
    repeated_endpoint_ratio = most_repeated / total_requests

    # --- Response time ---
    avg_response_time_ms = sum(response_times) / len(response_times) if response_times else 0

    # --- Session duration ---
    session_duration_sec = session_duration

    # --- Payload size ---
    avg_payload_size_bytes = sum(payload_sizes) / len(payload_sizes) if payload_sizes else 0

    # --- Login behavior ---
    login_failure_ratio = login_failures / max(login_attempts, 1)

    # --- Endpoint entropy (Shannon entropy) ---
    # High entropy = diverse endpoint access (human-like)
    # Low entropy = concentrated on one endpoint (bot-like)
    endpoint_entropy = _shannon_entropy(endpoint_counts, total_requests)

    # --- Request interval variance ---
    # Bots send at very regular intervals (low variance)
    # Humans have irregular clicking patterns (high variance)
    request_interval_variance = _variance(request_intervals)

    features = {
        "requests_per_minute": round(requests_per_minute, 4),
        "requests_per_second": round(requests_per_second, 4),
        "failed_request_ratio": round(failed_request_ratio, 4),
        "unique_endpoints": unique_endpoints,
        "repeated_endpoint_ratio": round(repeated_endpoint_ratio, 4),
        "avg_response_time_ms": round(avg_response_time_ms, 2),
        "session_duration_sec": round(session_duration_sec, 2),
        "avg_payload_size_bytes": round(avg_payload_size_bytes, 2),
        "login_attempts": login_attempts,
        "login_failure_ratio": round(login_failure_ratio, 4),
        "endpoint_entropy": round(endpoint_entropy, 4),
        "request_interval_variance": round(request_interval_variance, 6),
        "status_4xx_count": status_4xx_count,
    }

    logger.debug(f"Extracted features: {features}")
    return features


def _shannon_entropy(endpoint_counts: dict, total: int) -> float:
    """
    Shannon entropy of endpoint distribution.
    H = -sum(p * log2(p)) for each endpoint proportion p.
    Range: 0 (all requests to one endpoint) to log2(n) (uniform spread).
    """
    if total == 0 or not endpoint_counts:
        return 0.0
    entropy = 0.0
    for count in endpoint_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _variance(values: list) -> float:
    """Population variance of a list of numbers."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)
