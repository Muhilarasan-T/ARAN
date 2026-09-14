"""
ARAN — Normal User Traffic Simulator

Generates realistic human browsing behavior against the Demo Shopping API.
Sessions are characterized by:
- Moderate request rates (5–20 req/min)
- Diverse endpoint access (browses multiple sections)
- Low failure rate
- Natural time gaps between requests (variable intervals)
- Normal session duration (30–120 seconds)

Interview concept: Realistic simulation for ML validation
---------------------------------------------------------
We can't use real user traffic for a demo, so we simulate it.
The key is that simulated traffic must reflect the statistical properties
of real traffic — not just random noise. Human browsing has:
  - Long inter-request pauses (reading product pages)
  - High variance in interval timing
  - Diverse endpoint access patterns
  - Low failure rates
These properties become features the ML model uses to distinguish humans from bots.
"""
import asyncio
import random
import time
import logging
from collections import defaultdict

import httpx

logger = logging.getLogger("aran.simulation.normal")

DEMO_API_BASE = "http://localhost:8000/demo"

# Endpoints a normal user might visit, weighted by likelihood
HUMAN_ENDPOINTS = [
    ("/products", "GET", None),
    ("/search?q=keyboard", "GET", None),
    ("/search?q=headphones", "GET", None),
    ("/search?q=lamp", "GET", None),
    ("/product/1", "GET", None),
    ("/product/2", "GET", None),
    ("/product/3", "GET", None),
    ("/product/4", "GET", None),
    ("/product/5", "GET", None),
    ("/cart", "GET", None),
    ("/login", "POST", {"username": "alice", "password": "hunter2"}),
    ("/checkout", "POST", {"cart_items": [{"id": 1}], "payment_token": "demo_token"}),
]


async def simulate_normal_user(session_id: str, request_count: int = 30) -> dict:
    """
    Simulate a legitimate user session against the Demo API.

    Returns raw session stats dict to be passed to feature_extractor.
    """
    logger.info(f"[{session_id}] Simulating normal user ({request_count} requests)")

    # Session tracking
    session_start = time.time()
    total_requests = 0
    failed_requests = 0
    login_attempts = 0
    login_failures = 0
    endpoint_counts = defaultdict(int)
    response_times_ms = []
    request_intervals_sec = []
    payload_sizes_bytes = []
    status_4xx_count = 0

    last_request_time = time.time()

    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(request_count):
            endpoint, method, body = random.choice(HUMAN_ENDPOINTS)

            # Natural human gap between requests (0.5–8 seconds)
            delay = random.uniform(0.5, 8.0)
            await asyncio.sleep(delay)

            now = time.time()
            interval = now - last_request_time
            request_intervals_sec.append(interval)
            last_request_time = now

            try:
                req_start = time.perf_counter()
                if method == "GET":
                    resp = await client.get(f"{DEMO_API_BASE}{endpoint}")
                else:
                    resp = await client.post(f"{DEMO_API_BASE}{endpoint}", json=body)
                elapsed_ms = (time.perf_counter() - req_start) * 1000

                response_times_ms.append(elapsed_ms)
                endpoint_counts[endpoint.split("?")[0]] += 1
                payload_sizes_bytes.append(
                    len(resp.content) if hasattr(resp, "content") else random.randint(200, 2000)
                )

                total_requests += 1

                if endpoint == "/login":
                    login_attempts += 1

                if resp.status_code >= 400:
                    failed_requests += 1
                    status_4xx_count += 1
                    if endpoint == "/login":
                        login_failures += 1

            except Exception as e:
                logger.debug(f"Request failed: {e}")
                failed_requests += 1
                total_requests += 1
                response_times_ms.append(500.0)

    session_duration = time.time() - session_start

    return {
        "traffic_type": "human",
        "total_requests": total_requests,
        "session_duration_sec": session_duration,
        "failed_requests": failed_requests,
        "login_attempts": login_attempts,
        "login_failures": login_failures,
        "endpoint_counts": dict(endpoint_counts),
        "response_times_ms": response_times_ms,
        "request_intervals_sec": request_intervals_sec,
        "payload_sizes_bytes": payload_sizes_bytes,
        "status_4xx_count": status_4xx_count,
    }
