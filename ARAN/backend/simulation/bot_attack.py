"""
ARAN — Bot Attack Traffic Simulator

Generates realistic automated bot traffic against the Demo Shopping API.
Bot sessions are characterized by:
- Very high request rates (100–500 req/min)
- Concentrated on 1–2 endpoints (low diversity)
- Rapid-fire requests (near-zero interval, very low variance)
- High failure rate (credential stuffing / aggressive scraping)
- Short sessions

The simulator sends REAL HTTP requests to localhost — this is genuine
bot-like load generation, not fake numbers. The ML model observes the
actual behavioral differences.

Security notice: This simulator targets ONLY our local Demo API (localhost).
It must never be modified to target external systems.
"""
import asyncio
import random
import time
import logging
from collections import defaultdict

import httpx

logger = logging.getLogger("aran.simulation.bot")

DEMO_API_BASE = "http://localhost:8000/demo"

# Bot endpoints — credential stuffing + aggressive scraping of hot products
BOT_ENDPOINTS = [
    ("/login", "POST", {"username": f"user{i}", "password": "password123"})
    for i in range(1000)
] + [
    ("/product/1", "GET", None),
    ("/product/2", "GET", None),
    ("/products", "GET", None),
]


async def simulate_bot_attack(session_id: str, request_count: int = 100) -> dict:
    """
    Simulate an automated bot attack against the Demo API.

    Uses concurrent requests (asyncio gather) to achieve high request rates
    that are realistically bot-like.

    Returns raw session stats dict to be passed to feature_extractor.
    """
    logger.info(f"[{session_id}] Simulating bot attack ({request_count} requests)")

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

    # Bot attack pattern: 70% credential stuffing, 30% scraping
    bot_mode = "credential_stuffing" if random.random() < 0.7 else "scraping"
    logger.info(f"[{session_id}] Bot mode: {bot_mode}")

    last_request_time = time.time()
    lock = asyncio.Lock()

    async def make_request(client: httpx.AsyncClient, endpoint: str, method: str, body: dict):
        nonlocal total_requests, failed_requests, login_attempts, login_failures
        nonlocal status_4xx_count, last_request_time

        # Bot sends requests with near-zero delay (tiny jitter only)
        delay = random.uniform(0.01, 0.08)
        await asyncio.sleep(delay)

        now = time.time()
        async with lock:
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
            payload_sizes_bytes.append(len(resp.content) if hasattr(resp, "content") else 256)

            async with lock:
                total_requests += 1
                if endpoint == "/login":
                    login_attempts += 1
                if resp.status_code >= 400:
                    failed_requests += 1
                    status_4xx_count += 1
                    if endpoint == "/login":
                        login_failures += 1

        except Exception as e:
            logger.debug(f"Bot request failed: {e}")
            async with lock:
                failed_requests += 1
                total_requests += 1
            response_times_ms.append(100.0)

    # Build request queue
    tasks = []
    for _ in range(request_count):
        if bot_mode == "credential_stuffing":
            # Spam login endpoint
            entry = random.choice(BOT_ENDPOINTS[:1000])
            endpoint, method, body = entry
        else:
            # Scrape product listings
            entry = random.choice(BOT_ENDPOINTS[1000:])
            endpoint, method, body = entry

        tasks.append((endpoint, method, body))

    # Execute with concurrency limit (simulate 10 parallel bot threads)
    CONCURRENCY = 10
    async with httpx.AsyncClient(timeout=10.0) as client:
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def bounded_request(ep, meth, bdy):
            async with semaphore:
                await make_request(client, ep, meth, bdy)

        await asyncio.gather(*[bounded_request(ep, m, b) for ep, m, b in tasks])

    session_duration = time.time() - session_start

    return {
        "traffic_type": "bot",
        "bot_mode": bot_mode,
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
