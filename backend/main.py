"""
FastAPI application entry point.
Sets up CORS, lifespan events, health check, and includes all routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db, dispose_engine
from models.review import Review


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ai_code_review")


# ---------------------------------------------------------------------------
# Lifespan — Startup / Shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    # --- Startup ---
    logger.info("🚀 Starting AI Code Review Agent...")
    logger.info(f"   Environment: {settings.APP_ENV}")
    logger.info(f"   Database:    {settings.DATABASE_URL.split('@')[-1]}")

    # Create database tables
    await init_db()
    logger.info("✅ Database tables created/verified")

    yield

    # --- Shutdown ---
    logger.info("🛑 Shutting down AI Code Review Agent...")
    await dispose_engine()
    logger.info("✅ Database connections closed")


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Code Review Agent",
    description=(
        "Multi-agent AI pipeline that analyzes code changes on GitHub Pull Requests. "
        "Three specialized agents (Security, Performance, Quality) run in parallel "
        "via LangGraph, producing structured review feedback."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
from routers.webhook import router as webhook_router
from routers.reviews import router as reviews_router
from routers.analytics import router as analytics_router

app.include_router(webhook_router, prefix=settings.API_PREFIX)
app.include_router(reviews_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint",
    response_model=dict,
)
async def health_check():
    """Return application health status."""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.APP_ENV,
        },
        "error": None,
    }


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get(
    "/",
    tags=["System"],
    summary="Root endpoint",
)
async def root():
    """Welcome message and API info."""
    return {
        "success": True,
        "data": {
            "message": "AI Code Review Agent API",
            "docs": "/docs",
            "health": "/health",
        },
        "error": None,
    }
