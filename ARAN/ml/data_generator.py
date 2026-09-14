"""
ARAN — Synthetic Dataset Generator
====================================

What are we doing?
------------------
We're generating a synthetic (artificially created) dataset that mimics
the behavioral differences between legitimate human API users and bots.

Why not use a real dataset?
---------------------------
Real API traffic logs contain personal data and are difficult to share.
A well-designed synthetic dataset is:
  - Fully controlled (we choose the signal-to-noise ratio)
  - Shareable without privacy concerns
  - Reproducible (seed-controlled)
  - Portfolio-safe

What makes a good synthetic dataset?
--------------------------------------
Bad synthetic data: one feature perfectly separates classes → trivially easy
Good synthetic data: overlapping distributions, realistic noise, minority class
  that requires learning subtle combinations of features.

We achieve realism by:
  1. Drawing from different statistical distributions for humans vs bots
  2. Adding Gaussian noise to every feature
  3. Allowing some "clever bots" that look semi-human
  4. Allowing some "power users" that look bot-like

Output:
-------
  data/raw/traffic_dataset.csv — 5,000 rows × 14 columns

Run:
----
  cd ARAN/ml
  python data_generator.py
"""

import os
import random
import math
import numpy as np
import pandas as pd

# Reproducibility — fix seed so the dataset is identical every time you run this
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# Dataset size and class balance
N_HUMAN = 3000   # 60%
N_BOT = 2000     # 40%
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "traffic_dataset.csv")


# ===========================================================================
# Human session generators
# ===========================================================================

def generate_human_session() -> dict:
    """
    Generate features for one legitimate human session.

    Characteristics:
      - Low-moderate request rate (5–25 req/min)
      - High endpoint diversity (browsing multiple sections)
      - Low failure ratio
      - High session duration (reading pages, thinking)
      - High request interval variance (irregular clicking)
      - Low login attempts
    """
    session_duration = np.random.uniform(30, 300)       # 30s – 5 min
    total_requests = int(np.random.uniform(5, 80))
    requests_per_minute = (total_requests / session_duration) * 60
    requests_per_second = requests_per_minute / 60

    failed_request_ratio = np.clip(np.random.beta(1.5, 15), 0, 0.5)  # Low failure
    unique_endpoints = int(np.random.uniform(3, 8))
    repeated_endpoint_ratio = np.clip(np.random.beta(2, 5), 0.1, 0.8)
    avg_response_time_ms = np.random.uniform(80, 400)
    avg_payload_size_bytes = np.random.uniform(500, 5000)
    login_attempts = int(np.random.choice([0, 1, 2], p=[0.6, 0.35, 0.05]))
    login_failure_ratio = np.clip(np.random.beta(1, 8), 0, 0.5) if login_attempts > 0 else 0.0

    # High entropy = diverse endpoint access
    endpoint_entropy = np.random.uniform(1.5, 3.5)

    # High variance = irregular human clicking patterns
    request_interval_variance = np.random.uniform(0.5, 15.0)
    status_4xx_count = int(failed_request_ratio * total_requests)

    return {
        "requests_per_minute": round(requests_per_minute + np.random.normal(0, 2), 4),
        "requests_per_second": round(requests_per_second + np.random.normal(0, 0.05), 4),
        "failed_request_ratio": round(float(np.clip(failed_request_ratio, 0, 1)), 4),
        "unique_endpoints": unique_endpoints,
        "repeated_endpoint_ratio": round(float(np.clip(repeated_endpoint_ratio, 0, 1)), 4),
        "avg_response_time_ms": round(avg_response_time_ms + np.random.normal(0, 20), 2),
        "session_duration_sec": round(session_duration, 2),
        "avg_payload_size_bytes": round(avg_payload_size_bytes, 2),
        "login_attempts": login_attempts,
        "login_failure_ratio": round(login_failure_ratio, 4),
        "endpoint_entropy": round(float(np.clip(endpoint_entropy + np.random.normal(0, 0.2), 0.1, 5)), 4),
        "request_interval_variance": round(float(np.clip(request_interval_variance, 0, 50)), 6),
        "status_4xx_count": status_4xx_count,
        "is_bot": 0,
    }


# ===========================================================================
# Bot session generators
# ===========================================================================

def generate_bot_session(bot_type: str = None) -> dict:
    """
    Generate features for one bot session.

    Bot types:
      - credential_stuffing: login spammer, very high login attempts + failures
      - scraper: product/data harvester, very high rate on few endpoints
      - slow_bot: deliberate low-rate bot trying to evade detection

    Interview concept: Class imbalance and hard negatives
    ----------------------------------------------------
    Slow bots make the classification harder — they overlap with human sessions.
    This forces the model to learn subtle combinations of features, not just
    check one threshold. In a real interview, you'd mention "hard negatives"
    and explain that the model must generalize to evasive bot patterns.
    """
    if bot_type is None:
        bot_type = np.random.choice(
            ["credential_stuffing", "scraper", "slow_bot"],
            p=[0.45, 0.40, 0.15]
        )

    if bot_type == "credential_stuffing":
        session_duration = np.random.uniform(5, 60)
        total_requests = int(np.random.uniform(80, 500))
        failed_request_ratio = np.clip(np.random.beta(5, 3), 0.3, 0.99)
        unique_endpoints = int(np.random.choice([1, 2], p=[0.8, 0.2]))
        repeated_endpoint_ratio = np.clip(np.random.beta(10, 1), 0.8, 1.0)
        endpoint_entropy = np.random.uniform(0.0, 0.5)
        request_interval_variance = np.random.uniform(0.0001, 0.02)  # Near-zero
        login_attempts = int(np.random.uniform(50, 400))
        login_failure_ratio = np.clip(np.random.beta(8, 2), 0.5, 0.99)
        avg_response_time_ms = np.random.uniform(50, 200)
        avg_payload_size_bytes = np.random.uniform(50, 300)  # Small credential payloads

    elif bot_type == "scraper":
        session_duration = np.random.uniform(3, 30)
        total_requests = int(np.random.uniform(100, 800))
        failed_request_ratio = np.clip(np.random.beta(2, 8), 0.05, 0.30)
        unique_endpoints = int(np.random.choice([1, 2, 3], p=[0.5, 0.35, 0.15]))
        repeated_endpoint_ratio = np.clip(np.random.beta(9, 2), 0.7, 1.0)
        endpoint_entropy = np.random.uniform(0.0, 1.0)
        request_interval_variance = np.random.uniform(0.0001, 0.05)
        login_attempts = 0
        login_failure_ratio = 0.0
        avg_response_time_ms = np.random.uniform(40, 150)
        avg_payload_size_bytes = np.random.uniform(1000, 8000)  # Large scraped pages

    else:  # slow_bot — deliberate evasion
        session_duration = np.random.uniform(60, 200)
        total_requests = int(np.random.uniform(10, 40))
        failed_request_ratio = np.clip(np.random.beta(2, 6), 0.1, 0.50)
        unique_endpoints = int(np.random.uniform(1, 4))
        repeated_endpoint_ratio = np.clip(np.random.beta(5, 3), 0.4, 0.95)
        endpoint_entropy = np.random.uniform(0.3, 1.5)
        request_interval_variance = np.random.uniform(0.05, 0.8)  # Some variance to evade
        login_attempts = int(np.random.choice([0, 1, 5, 10], p=[0.4, 0.2, 0.2, 0.2]))
        login_failure_ratio = np.clip(np.random.beta(4, 4), 0.2, 0.75) if login_attempts > 0 else 0.0
        avg_response_time_ms = np.random.uniform(80, 350)
        avg_payload_size_bytes = np.random.uniform(300, 3000)

    requests_per_minute = (total_requests / session_duration) * 60
    requests_per_second = requests_per_minute / 60
    status_4xx_count = int(failed_request_ratio * total_requests)

    return {
        "requests_per_minute": round(float(np.clip(requests_per_minute + np.random.normal(0, 5), 0, 1000)), 4),
        "requests_per_second": round(float(np.clip(requests_per_second + np.random.normal(0, 0.1), 0, 30)), 4),
        "failed_request_ratio": round(float(np.clip(failed_request_ratio, 0, 1)), 4),
        "unique_endpoints": unique_endpoints,
        "repeated_endpoint_ratio": round(float(np.clip(repeated_endpoint_ratio, 0, 1)), 4),
        "avg_response_time_ms": round(float(np.clip(avg_response_time_ms + np.random.normal(0, 10), 10, 2000)), 2),
        "session_duration_sec": round(session_duration, 2),
        "avg_payload_size_bytes": round(avg_payload_size_bytes, 2),
        "login_attempts": login_attempts,
        "login_failure_ratio": round(float(np.clip(login_failure_ratio, 0, 1)), 4),
        "endpoint_entropy": round(float(np.clip(endpoint_entropy + np.random.normal(0, 0.1), 0, 5)), 4),
        "request_interval_variance": round(float(np.clip(request_interval_variance, 0, 50)), 6),
        "status_4xx_count": status_4xx_count,
        "is_bot": 1,
    }


# ===========================================================================
# Main generation
# ===========================================================================

def generate_dataset(n_human: int = N_HUMAN, n_bot: int = N_BOT) -> pd.DataFrame:
    """
    Generate the full synthetic traffic dataset.

    Interview concept: Why do we separate train/test AFTER generation?
    -------------------------------------------------------------------
    We generate ALL data here, then split later in train.py.
    This ensures test data was never seen during training — no data leakage.
    If we generated train/test separately, there's a risk of distribution
    inconsistency. Generating together, then splitting, is cleaner.
    """
    print(f"Generating {n_human} human sessions and {n_bot} bot sessions…")

    human_sessions = [generate_human_session() for _ in range(n_human)]
    bot_sessions = [generate_bot_session() for _ in range(n_bot)]

    df = pd.DataFrame(human_sessions + bot_sessions)

    # Shuffle so humans/bots aren't in blocks
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    # Clip any physically impossible values
    df["requests_per_minute"] = df["requests_per_minute"].clip(lower=0)
    df["requests_per_second"] = df["requests_per_second"].clip(lower=0)
    df["failed_request_ratio"] = df["failed_request_ratio"].clip(0, 1)
    df["repeated_endpoint_ratio"] = df["repeated_endpoint_ratio"].clip(0, 1)
    df["login_failure_ratio"] = df["login_failure_ratio"].clip(0, 1)
    df["endpoint_entropy"] = df["endpoint_entropy"].clip(lower=0)
    df["request_interval_variance"] = df["request_interval_variance"].clip(lower=0)

    print(f"Dataset shape: {df.shape}")
    print(f"Class distribution:\n{df['is_bot'].value_counts()}")
    print(f"\nFeature stats:\n{df.describe().T[['mean', 'std', 'min', 'max']].round(3)}")

    return df


if __name__ == "__main__":
    df = generate_dataset()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✅ Dataset saved to: {OUTPUT_PATH}")
