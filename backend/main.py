"""
main.py - FastAPI entry point for SecInt v2 Threat Intelligence API
"""
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file (no-op in production where env vars are set directly)
load_dotenv()

from database import connect_db, disconnect_db
from routers import ingestion, iocs, reports
from services.api_validator import api_validator
from services.demo_seeder import seed_demo_data
from services.scheduler import get_scheduler_status, start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _cors_origins() -> list:
    """
    Build the CORS allow-list from the CORS_ORIGINS env var (comma-separated),
    falling back to sensible defaults that cover localhost dev + Vercel deploy.
    """
    env_val = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in env_val.split(",") if o.strip()]
    if not origins:
        origins = [
            "http://localhost:3000",
            "http://frontend:3000",
        ]
    origins.append("https://*.vercel.app")
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()

    # Seed demo data if the collection is empty or no API keys are configured
    seeded = await seed_demo_data()
    if seeded:
        logger.info("🌱 Demo dataset loaded: %d IOCs available immediately.", seeded)

    # Start the background refresh scheduler
    refresh_hours = int(os.getenv("REFRESH_INTERVAL_HOURS", "6"))
    start_scheduler(interval_hours=refresh_hours)

    yield

    # Shutdown
    stop_scheduler()
    await disconnect_db()


app = FastAPI(
    title="SecInt v2 - Threat Intelligence API",
    description=(
        "Real-time threat intelligence platform with IOC extraction, "
        "enrichment, and severity scoring. "
        "Demo mode active when no API keys are configured."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(iocs.router, prefix="/api/iocs", tags=["IOCs"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["Ingestion"])


@app.get("/")
async def root():
    demo_mode = not bool(
        os.getenv("OTX_API_KEY") or
        os.getenv("VIRUSTOTAL_API_KEY") or
        os.getenv("ABUSEIPDB_API_KEY")
    )
    return {
        "message": "SecInt v2 - Real-time Threat Intelligence API",
        "version": "2.0.0",
        "status": "running",
        "demo_mode": demo_mode,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/health/apis")
async def api_health(use_cache: bool = True):
    """Check health status of all external threat intelligence APIs."""
    health_status = await api_validator.validate_all_apis(use_cache=use_cache)
    overall_status = api_validator.get_overall_status(health_status)
    return {
        "overall_status": overall_status,
        "apis": health_status,
        "last_checked": api_validator.last_check.isoformat() if api_validator.last_check else None,
    }


@app.get("/health/scheduler")
async def scheduler_health():
    """Return the current state of the background IOC refresh scheduler."""
    return get_scheduler_status()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
