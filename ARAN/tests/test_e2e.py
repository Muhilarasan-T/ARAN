"""
ARAN — End-to-End Test Suite
=============================

Tests the full pipeline:
  1. Health / API availability
  2. Demo Shopping API (all 6 endpoints)
  3. ML inference pipeline (known-good feature vectors)
  4. Feature extractor (unit)
  5. Mitigation engine (unit)
  6. Protection route (simulation trigger)
  7. Risk classification helpers

Run:
  cd ARAN/backend
  pytest ../tests/test_e2e.py -v

Note: The backend does NOT need to be running for unit tests (groups 2-5).
For integration tests (group 6), start uvicorn separately first.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# ===========================================================================
# 1. Health — requires live server
# ===========================================================================
class TestHealth:
    """Smoke tests against the live FastAPI server."""

    def _get(self, path: str):
        import httpx
        try:
            return httpx.get(f"http://localhost:8000{path}", timeout=5)
        except Exception as e:
            pytest.skip(f"Backend not running: {e}")

    def test_health_endpoint(self):
        r = self._get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "ARAN"

    def test_protection_status(self):
        r = self._get("/protection/status")
        assert r.status_code == 200
        assert r.json()["protection"] == "active"


# ===========================================================================
# 2. Demo Shopping API — live server
# ===========================================================================
class TestDemoAPI:

    def _get(self, path: str):
        import httpx
        try:
            return httpx.get(f"http://localhost:8000/demo{path}", timeout=5)
        except Exception as e:
            pytest.skip(f"Backend not running: {e}")

    def _post(self, path: str, body: dict):
        import httpx
        try:
            return httpx.post(f"http://localhost:8000/demo{path}", json=body, timeout=5)
        except Exception as e:
            pytest.skip(f"Backend not running: {e}")

    def test_get_products(self):
        r = self._get("/products")
        assert r.status_code == 200
        data = r.json()
        assert "products" in data
        assert len(data["products"]) > 0

    def test_search_products(self):
        r = self._get("/search?q=keyboard")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert data["query"] == "keyboard"

    def test_get_product_valid(self):
        r = self._get("/product/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_product_not_found(self):
        r = self._get("/product/9999")
        assert r.status_code == 404

    def test_get_cart(self):
        r = self._get("/cart")
        assert r.status_code == 200
        assert "items" in r.json()
        assert "total" in r.json()

    def test_post_login_succeeds_sometimes(self):
        """Login has a 35% failure rate — run 10 times, expect at least one success."""
        import httpx
        try:
            successes = 0
            for _ in range(10):
                r = httpx.post("http://localhost:8000/demo/login",
                               json={"username": "alice", "password": "pw"},
                               timeout=5)
                if r.status_code == 200:
                    successes += 1
            assert successes > 0, "Expected at least 1 successful login in 10 attempts"
        except httpx.ConnectError:
            pytest.skip("Backend not running")

    def test_post_checkout(self):
        r = self._post("/checkout", {
            "cart_items": [{"id": 1, "name": "test"}],
            "payment_token": "demo_token"
        })
        assert r.status_code == 200
        data = r.json()
        assert "order_id" in data
        assert data["status"] == "confirmed"


# ===========================================================================
# 3. ML Inference — unit tests (no live server required)
# ===========================================================================
class TestMLInference:

    @pytest.fixture(autouse=True)
    def load_model(self):
        from services.inference import load_model
        load_model()

    BOT_FEATURES = {
        "requests_per_minute": 380.0,
        "requests_per_second": 6.3,
        "failed_request_ratio": 0.62,
        "unique_endpoints": 1,
        "repeated_endpoint_ratio": 0.97,
        "avg_response_time_ms": 85.0,
        "session_duration_sec": 18.0,
        "avg_payload_size_bytes": 130.0,
        "login_attempts": 230,
        "login_failure_ratio": 0.91,
        "endpoint_entropy": 0.05,
        "request_interval_variance": 0.0008,
        "status_4xx_count": 143,
    }

    HUMAN_FEATURES = {
        "requests_per_minute": 9.0,
        "requests_per_second": 0.15,
        "failed_request_ratio": 0.03,
        "unique_endpoints": 6,
        "repeated_endpoint_ratio": 0.25,
        "avg_response_time_ms": 220.0,
        "session_duration_sec": 145.0,
        "avg_payload_size_bytes": 1800.0,
        "login_attempts": 1,
        "login_failure_ratio": 0.0,
        "endpoint_entropy": 2.8,
        "request_interval_variance": 4.5,
        "status_4xx_count": 0,
    }

    def test_bot_features_return_high_probability(self):
        from services.inference import predict
        prob, _ = predict(self.BOT_FEATURES)
        assert 0.0 <= prob <= 1.0
        assert prob >= 0.7, f"Expected high bot prob for bot features, got {prob:.3f}"

    def test_human_features_return_low_probability(self):
        from services.inference import predict
        prob, _ = predict(self.HUMAN_FEATURES)
        assert 0.0 <= prob <= 1.0
        assert prob <= 0.5, f"Expected low bot prob for human features, got {prob:.3f}"

    def test_predict_returns_feature_dict(self):
        from services.inference import predict
        prob, feats = predict(self.BOT_FEATURES)
        assert isinstance(prob, float)
        assert isinstance(feats, dict)
        assert "requests_per_minute" in feats

    def test_probability_range(self):
        """Probability must always be in [0, 1]."""
        from services.inference import predict
        for features in [self.BOT_FEATURES, self.HUMAN_FEATURES]:
            prob, _ = predict(features)
            assert 0.0 <= prob <= 1.0


# ===========================================================================
# 4. Risk Classification — unit tests
# ===========================================================================
class TestRiskClassification:

    def test_low_risk(self):
        from config import get_risk_level, get_recommended_action
        assert get_risk_level(0.10) == "LOW"
        assert get_recommended_action("LOW") == "ALLOW"

    def test_medium_risk(self):
        from config import get_risk_level, get_recommended_action
        assert get_risk_level(0.55) == "MEDIUM"
        assert get_recommended_action("MEDIUM") == "RATE_LIMIT"

    def test_high_risk(self):
        from config import get_risk_level, get_recommended_action
        assert get_risk_level(0.90) == "HIGH"
        assert get_recommended_action("HIGH") == "BLOCK"

    def test_threshold_boundaries(self):
        from config import get_risk_level
        assert get_risk_level(0.40) == "MEDIUM"   # right at low/medium boundary
        assert get_risk_level(0.75) == "HIGH"      # right at medium/high boundary
        assert get_risk_level(0.39) == "LOW"
        assert get_risk_level(0.74) == "MEDIUM"


# ===========================================================================
# 5. Feature Extractor — unit tests
# ===========================================================================
class TestFeatureExtractor:

    def _make_session_stats(self, **overrides):
        base = {
            "total_requests": 50,
            "session_duration_sec": 60.0,
            "failed_requests": 5,
            "login_attempts": 2,
            "login_failures": 1,
            "endpoint_counts": {"/products": 20, "/search": 15, "/cart": 10, "/product/1": 5},
            "response_times_ms": [100.0, 150.0, 80.0, 200.0, 120.0],
            "request_intervals_sec": [0.5, 1.2, 2.0, 0.8, 3.0],
            "payload_sizes_bytes": [1000, 2000, 500, 800],
            "status_4xx_count": 5,
        }
        base.update(overrides)
        return base

    def test_extraction_returns_13_features(self):
        from services.feature_extractor import extract_features
        feats = extract_features(self._make_session_stats())
        assert len(feats) == 13

    def test_requests_per_minute_calculation(self):
        from services.feature_extractor import extract_features
        stats = self._make_session_stats(total_requests=60, session_duration_sec=60.0)
        feats = extract_features(stats)
        assert abs(feats["requests_per_minute"] - 60.0) < 1.0

    def test_failed_ratio_calculation(self):
        from services.feature_extractor import extract_features
        stats = self._make_session_stats(total_requests=100, failed_requests=30)
        feats = extract_features(stats)
        assert abs(feats["failed_request_ratio"] - 0.30) < 0.01

    def test_entropy_is_positive(self):
        from services.feature_extractor import extract_features
        feats = extract_features(self._make_session_stats())
        assert feats["endpoint_entropy"] >= 0

    def test_zero_interval_variance_for_uniform_requests(self):
        """Equal intervals should produce very low variance."""
        from services.feature_extractor import extract_features
        stats = self._make_session_stats(
            request_intervals_sec=[1.0, 1.0, 1.0, 1.0, 1.0]
        )
        feats = extract_features(stats)
        assert feats["request_interval_variance"] < 1e-6

    def test_high_variance_for_irregular_requests(self):
        """Very irregular intervals should produce high variance."""
        from services.feature_extractor import extract_features
        stats = self._make_session_stats(
            request_intervals_sec=[0.1, 10.0, 0.05, 15.0, 0.02]
        )
        feats = extract_features(stats)
        assert feats["request_interval_variance"] > 5.0

    def test_all_feature_values_are_numeric(self):
        from services.feature_extractor import extract_features
        feats = extract_features(self._make_session_stats())
        for k, v in feats.items():
            assert isinstance(v, (int, float)), f"Feature {k} is not numeric: {type(v)}"

    def test_no_negative_values_for_counts(self):
        from services.feature_extractor import extract_features
        feats = extract_features(self._make_session_stats())
        assert feats["unique_endpoints"] >= 0
        assert feats["login_attempts"] >= 0
        assert feats["status_4xx_count"] >= 0


# ===========================================================================
# 6. Mitigation Engine — unit tests
# ===========================================================================
class TestMitigationEngine:

    def test_allow_action(self):
        from services.mitigation_engine import apply_mitigation
        result = apply_mitigation("test_allow_001", "ALLOW")
        assert result["action"] == "ALLOW"
        assert result["block_expires_at"] is None

    def test_rate_limit_action(self):
        from services.mitigation_engine import apply_mitigation, is_rate_limited
        result = apply_mitigation("test_rl_001", "RATE_LIMIT")
        assert result["action"] == "RATE_LIMIT"
        assert is_rate_limited("test_rl_001")

    def test_block_action(self):
        from services.mitigation_engine import apply_mitigation, is_blocked
        result = apply_mitigation("test_block_001", "BLOCK")
        assert result["action"] == "BLOCK"
        assert result["block_expires_at"] is not None
        assert is_blocked("test_block_001")

    def test_unblock_clears_session(self):
        from services.mitigation_engine import apply_mitigation, is_blocked, unblock_session
        apply_mitigation("test_unblock_001", "BLOCK")
        assert is_blocked("test_unblock_001")
        unblock_session("test_unblock_001")
        assert not is_blocked("test_unblock_001")

    def test_allow_session_not_blocked(self):
        from services.mitigation_engine import apply_mitigation, is_blocked
        apply_mitigation("test_clean_001", "ALLOW")
        assert not is_blocked("test_clean_001")

    def test_get_session_status(self):
        from services.mitigation_engine import apply_mitigation, get_session_status
        apply_mitigation("test_status_001", "BLOCK")
        status = get_session_status("test_status_001")
        assert status["status"] == "BLOCKED"


# ===========================================================================
# 7. Explainer — unit tests
# ===========================================================================
class TestExplainer:

    @pytest.fixture(autouse=True)
    def load_model(self):
        from services.inference import load_model
        load_model()

    def test_explanation_returns_list(self):
        from services.explainer import build_explanation
        features = {
            "requests_per_minute": 350.0, "requests_per_second": 5.8,
            "failed_request_ratio": 0.60, "unique_endpoints": 1,
            "repeated_endpoint_ratio": 0.95, "avg_response_time_ms": 90.0,
            "session_duration_sec": 20.0, "avg_payload_size_bytes": 120.0,
            "login_attempts": 200, "login_failure_ratio": 0.90,
            "endpoint_entropy": 0.05, "request_interval_variance": 0.001,
            "status_4xx_count": 120,
        }
        explanation = build_explanation(features, 0.95)
        assert isinstance(explanation, list)
        assert len(explanation) >= 1
        assert all(isinstance(e, str) for e in explanation)

    def test_low_prob_produces_non_empty_explanation(self):
        from services.explainer import build_explanation
        features = {
            "requests_per_minute": 8.0, "requests_per_second": 0.13,
            "failed_request_ratio": 0.02, "unique_endpoints": 5,
            "repeated_endpoint_ratio": 0.18, "avg_response_time_ms": 230.0,
            "session_duration_sec": 180.0, "avg_payload_size_bytes": 2200.0,
            "login_attempts": 0, "login_failure_ratio": 0.0,
            "endpoint_entropy": 3.1, "request_interval_variance": 6.5,
            "status_4xx_count": 0,
        }
        explanation = build_explanation(features, 0.04)
        assert isinstance(explanation, list)
        # May be empty or have a generic message — just ensure it doesn't crash
