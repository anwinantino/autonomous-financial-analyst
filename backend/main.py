"""
main.py — FastAPI application entry point.

Registers routers for /predict and /analyze endpoints,
configures CORS, and provides the /health check.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import predict, analyze

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log startup / shutdown events."""
    logger.info("Autonomous Financial Analyst backend starting up.")
    yield
    logger.info("Backend shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Autonomous Financial Analyst",
    description="Hybrid ML + LLM financial forecasting API.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow all origins for Vercel preview environments and localhost.
# In a strict production environment, this should be restricted.
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(predict.router)
app.include_router(analyze.router)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns OK status. Used by Docker health checks and Render."""
    return {"status": "ok"}
