"""
ingestion.py - Trigger and monitor threat intelligence ingestion.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from services.direct_ingest import DirectThreatIngestionService

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared state — simple enough for a single-worker free-tier deploy
_status = {
    "running": False,
    "progress": None,
    "last_run": None,
    "last_result": None,
}


class IngestionResult(BaseModel):
    status: str
    message: str
    stats: Optional[dict] = None


async def _run_ingestion_background() -> None:
    """
    Run ingestion in background. DB is already connected via the app lifespan —
    do NOT call connect_db() / disconnect_db() here.
    """
    global _status
    _status["running"] = True
    _status["progress"] = "Starting…"

    try:
        service = DirectThreatIngestionService()

        _status["progress"] = "Fetching OTX pulses…"
        await service.ingest_otx_pulses(limit=20)

        _status["progress"] = "Fetching URLhaus URLs…"
        await service.ingest_urlhaus_urls(limit=50)

        _status["progress"] = "Fetching URLhaus payloads…"
        await service.ingest_urlhaus_payloads(limit=50)

        _status["last_result"] = {"status": "success", "stats": service.stats}
        _status["progress"] = "Completed"
        logger.info("✅ Manual ingestion completed: %s", service.stats)

    except Exception as exc:
        logger.error("❌ Manual ingestion failed: %s", exc, exc_info=True)
        _status["last_result"] = {"status": "error", "error": str(exc)}
        _status["progress"] = f"Error: {exc}"
    finally:
        _status["running"] = False
        _status["last_run"] = datetime.now(timezone.utc).isoformat()


@router.post("/trigger", response_model=IngestionResult)
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """
    Trigger a manual IOC ingestion run across all configured feeds.
    Returns immediately — poll /status to track progress.
    """
    if _status["running"]:
        raise HTTPException(
            status_code=409,
            detail="Ingestion is already running. Poll /api/ingestion/status to monitor progress.",
        )
    background_tasks.add_task(_run_ingestion_background)
    return IngestionResult(
        status="started",
        message="Ingestion started in background. Poll /api/ingestion/status for updates.",
    )


@router.get("/status")
async def ingestion_status():
    """Current ingestion state."""
    return _status
