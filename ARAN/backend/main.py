"""
ARAN Backend — Main Application Entry Point

This is the FastAPI application root. It wires together:
- Demo Shopping API routes
- Protection / inference routes
- Mitigation routes
- WebSocket real-time endpoint
- CORS middleware
- Startup model loading
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from services.inference import load_model
from routes.demo_api import router as demo_router
from routes.protection import router as protection_router
from routes.mitigation import router as mitigation_router
from websocket.manager import router as ws_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("aran")


# ---------------------------------------------------------------------------
# Lifespan — runs ONCE at startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading ML model and preprocessor…")
    load_model()          # Loads model into memory — never trains at request time
    logger.info("ARAN backend ready.")
    yield
    logger.info("ARAN backend shutting down.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ARAN API",
    description="Real-Time API Bot Detection & Automated Mitigation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(demo_router,       prefix="/demo",       tags=["Demo API"])
app.include_router(protection_router, prefix="/protection", tags=["Protection"])
app.include_router(mitigation_router, prefix="/mitigation", tags=["Mitigation"])
app.include_router(ws_router,                               tags=["WebSocket"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "ARAN"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level,
    )
