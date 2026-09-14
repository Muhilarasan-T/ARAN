"""
ARAN — Feature Engineering
============================

What are we doing?
------------------
We define and document every behavioral feature used by the XGBoost model.
This file is reference documentation — the actual features are computed by
data_generator.py (offline training) and services/feature_extractor.py (live inference).

Why is feature engineering important?
--------------------------------------
Raw data rarely feeds directly into ML models.
Good features encode domain knowledge that helps the model learn faster
and generalize better. For bot detection, the key insight is:

  "Bots and humans behave differently — our job is to quantify that difference."

Feature dictionary:
-------------------
Each feature below includes:
  - What it measures
  - Why bots differ from humans on this feature
  - Expected range
"""

# ===========================================================================
# Feature Definitions (used as documentation + inference validation)
# ===========================================================================

FEATURE_SCHEMA = {
    "requests_per_minute": {
        "description": "Total requests normalized to a 60-second window",
        "type": "continuous",
        "human_range": "5–25",
        "bot_range": "80–800+",
        "intuition": "Bots never take breaks. Humans read pages, think, type. "
                     "A human who hits the API 500 times per minute is almost certainly a bot.",
    },
    "requests_per_second": {
        "description": "Burst request rate — captures short-window spikes",
        "type": "continuous",
        "human_range": "0.1–0.5",
        "bot_range": "2–15+",
        "intuition": "Even fast typers can't click 5+ times per second consistently.",
    },
    "failed_request_ratio": {
        "description": "Proportion of requests that returned 4xx/5xx status codes",
        "type": "continuous",
        "human_range": "0–0.1",
        "bot_range": "0.3–0.95",
        "intuition": "Credential stuffers try thousands of username/password combos — "
                     "most fail. Scrapers hit endpoints with invalid params.",
    },
    "unique_endpoints": {
        "description": "Number of distinct API paths accessed in the session",
        "type": "discrete",
        "human_range": "3–8",
        "bot_range": "1–3",
        "intuition": "A human shopping on an e-commerce site visits products, searches, "
                     "checks cart, looks at checkout. A bot targeting /login only visits one endpoint.",
    },
    "repeated_endpoint_ratio": {
        "description": "Requests to the most-hit endpoint / total requests",
        "type": "continuous",
        "human_range": "0.1–0.5",
        "bot_range": "0.7–1.0",
        "intuition": "If 95% of your requests go to /login, you're probably a bot.",
    },
    "avg_response_time_ms": {
        "description": "Mean backend response time across the session",
        "type": "continuous",
        "human_range": "100–400ms",
        "bot_range": "40–200ms",
        "intuition": "Bots don't wait for page rendering. They make raw API calls "
                     "and process responses programmatically — often faster.",
    },
    "session_duration_sec": {
        "description": "Total time from first to last request in session",
        "type": "continuous",
        "human_range": "30–300s",
        "bot_range": "3–30s",
        "intuition": "A human shopping trip takes minutes. A bot credential stuffing "
                     "400 login attempts might finish in 10 seconds.",
    },
    "avg_payload_size_bytes": {
        "description": "Mean size of request payloads",
        "type": "continuous",
        "human_range": "500–5000 bytes",
        "bot_range": "Varies by bot type",
        "intuition": "Credential stuffers send tiny JSON bodies. Scrapers may send "
                     "nothing (GET) or receive very large responses.",
    },
    "login_attempts": {
        "description": "Count of POST /login calls in the session",
        "type": "discrete",
        "human_range": "0–2",
        "bot_range": "50–400+",
        "intuition": "A human logs in once or twice. A credential stuffer tries "
                     "thousands of username/password combinations.",
    },
    "login_failure_ratio": {
        "description": "Failed login attempts / total login attempts",
        "type": "continuous",
        "human_range": "0–0.2",
        "bot_range": "0.5–0.99",
        "intuition": "If you fail to login 95% of the time, you're trying passwords "
                     "from a leaked credential list — not a real user.",
    },
    "endpoint_entropy": {
        "description": "Shannon entropy of endpoint access distribution. "
                       "High = diverse access; Low = concentrated on few endpoints.",
        "type": "continuous",
        "human_range": "1.5–3.5",
        "bot_range": "0.0–1.0",
        "intuition": "H = -sum(p * log2(p)). If all requests go to one endpoint, "
                     "entropy ≈ 0. If spread evenly across 8 endpoints, entropy is high.",
    },
    "request_interval_variance": {
        "description": "Statistical variance of time gaps between consecutive requests",
        "type": "continuous",
        "human_range": "0.5–15.0",
        "bot_range": "0.0001–0.05",
        "intuition": "Humans click irregularly — sometimes fast, sometimes slow. "
                     "Bots use a fixed loop or sleep(0.01) — nearly zero variance. "
                     "This is one of the most powerful features for detecting evasive bots.",
    },
    "status_4xx_count": {
        "description": "Raw count of 4xx status responses",
        "type": "discrete",
        "human_range": "0–3",
        "bot_range": "20–500+",
        "intuition": "Correlated with failed_request_ratio but captures absolute volume. "
                     "Useful for detecting bots even in short sessions.",
    },
}

FEATURE_COLUMNS = list(FEATURE_SCHEMA.keys())  # 13 features, excludes 'is_bot'
TARGET_COLUMN = "is_bot"


def print_feature_guide():
    """Print a formatted feature reference guide."""
    print("\n" + "="*70)
    print("ARAN — Feature Engineering Guide")
    print("="*70)
    for feat, info in FEATURE_SCHEMA.items():
        print(f"\n📌 {feat}")
        print(f"   Description: {info['description']}")
        print(f"   Human range: {info['human_range']}")
        print(f"   Bot range:   {info['bot_range']}")
        print(f"   Intuition:   {info['intuition']}")
    print("\n" + "="*70)


if __name__ == "__main__":
    print_feature_guide()
    print(f"\nTotal features: {len(FEATURE_COLUMNS)}")
    print(f"Feature names: {FEATURE_COLUMNS}")
