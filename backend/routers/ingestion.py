"""
ingestion.py - API endpoints for triggering threat intelligence ingestion
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from services.direct_ingest import DirectThreatIngestionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Track ingestion status
ingestion_status = {
    "running": False,
    "progress": None,
    "last_run": None,
    "last_result": None
}

class IngestionResult(BaseModel):
    status: str
    message: str
    stats: Optional[dict] = None

async def run_ingestion_background():
    """Run ingestion in background"""
    global ingestion_status
    
    try:
        ingestion_status["running"] = True
        ingestion_status["progress"] = "Starting ingestion..."
        logger.info("Starting background ingestion...")
        
        from database import connect_db, disconnect_db
        await connect_db()
        
        service = DirectThreatIngestionService()
        
        # Update progress for each step
        ingestion_status["progress"] = "Fetching OTX pulses..."
        await service.ingest_otx_pulses(limit=20)  # Reduced from 50 to 20 for speed
        
        ingestion_status["progress"] = "Fetching URLhaus URLs..."
        await service.ingest_urlhaus_urls(limit=50)  # Reduced from 100 to 50
        
        ingestion_status["progress"] = "Fetching URLhaus payloads..."
        await service.ingest_urlhaus_payloads(limit=50)  # Reduced from 100 to 50
        
        await disconnect_db()
        
        ingestion_status["last_result"] = {
            "status": "success",
            "stats": service.stats
        }
        ingestion_status["progress"] = "Completed"
        logger.info(f"Background ingestion completed successfully: {service.stats}")
        
    except Exception as e:
        logger.error(f"Background ingestion failed: {e}")
        ingestion_status["last_result"] = {
            "status": "error",
            "error": str(e)
        }
        ingestion_status["progress"] = f"Error: {str(e)}"
    finally:
        ingestion_status["running"] = False
        from datetime import datetime
        ingestion_status["last_run"] = datetime.utcnow().isoformat()

@router.post("/trigger", response_model=IngestionResult)
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """
    Trigger threat intelligence ingestion from all sources
    
    This endpoint starts ingestion in the background and returns immediately.
    Check /status endpoint to monitor progress.
    """
    if ingestion_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="Ingestion is already running. Please wait for it to complete."
        )
    
    # Start ingestion in background
    background_tasks.add_task(run_ingestion_background)
    
    return IngestionResult(
        status="started",
        message="Threat intelligence ingestion started in background"
    )

@router.get("/status")
async def ingestion_status_endpoint():
    """
    Get current ingestion status
    
    Returns information about running/last ingestion
    """
    return ingestion_status
