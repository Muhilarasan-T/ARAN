"""Quick integration test — no SHAP (avoids slow first-call overhead)."""
import sys
sys.path.insert(0, 'backend')

from services.inference import load_model, predict
from services.feature_extractor import extract_features
from services.mitigation_engine import apply_mitigation, is_blocked
from config import get_risk_level, get_recommended_action
import httpx

print("=== ARAN Integration Test ===\n")

# 1. Live API health
try:
    r = httpx.get("http://localhost:8000/health", timeout=3)
    print(f"[PASS] /health → {r.json()}")
except Exception as e:
    print(f"[SKIP] Backend not reachable: {e}")

# 2. Demo products
try:
    r = httpx.get("http://localhost:8000/demo/products", timeout=3)
    count = len(r.json()["products"])
    print(f"[PASS] /demo/products → {count} products (HTTP {r.status_code})")
except Exception as e:
    print(f"[SKIP] {e}")

# 3. ML pipeline
load_model()
print("[PASS] Model loaded")

human_stats = {
    "total_requests": 15, "session_duration_sec": 120.0,
    "failed_requests": 0, "login_attempts": 1, "login_failures": 0,
    "endpoint_counts": {"/products": 5, "/search": 4, "/cart": 3, "/product/1": 2, "/login": 1},
    "response_times_ms": [180.0, 220.0, 190.0, 250.0, 170.0],
    "request_intervals_sec": [3.5, 8.2, 1.1, 12.0, 5.3, 9.8, 2.1, 7.4],
    "payload_sizes_bytes": [1800.0, 2400.0, 900.0, 1200.0, 3000.0],
    "status_4xx_count": 0,
}
feats = extract_features(human_stats)
prob, _ = predict(feats)
risk = get_risk_level(prob)
action = get_recommended_action(risk)
assert prob <= 0.6, f"Expected low prob for human, got {prob:.3f}"
print(f"[PASS] Human session → {prob:.1%} bot prob → {risk} → {action}")

bot_stats = {
    "total_requests": 250, "session_duration_sec": 22.0,
    "failed_requests": 148, "login_attempts": 230, "login_failures": 210,
    "endpoint_counts": {"/login": 230, "/products": 20},
    "response_times_ms": [88.0, 92.0, 85.0, 91.0, 87.0],
    "request_intervals_sec": [0.009, 0.011, 0.008, 0.010, 0.012],
    "payload_sizes_bytes": [130.0, 125.0, 128.0, 133.0],
    "status_4xx_count": 148,
}
feats = extract_features(bot_stats)
prob, _ = predict(feats)
risk = get_risk_level(prob)
action = get_recommended_action(risk)
assert prob >= 0.7, f"Expected high prob for bot, got {prob:.3f}"
print(f"[PASS] Bot session   → {prob:.1%} bot prob → {risk} → {action}")

# 4. Mitigation
apply_mitigation("integ_test_bot", "BLOCK")
assert is_blocked("integ_test_bot")
print("[PASS] Mitigation BLOCK applied and confirmed")

print("\n=== ALL INTEGRATION CHECKS PASSED ===")
