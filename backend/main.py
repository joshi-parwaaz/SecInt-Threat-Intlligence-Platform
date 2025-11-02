"""
main.py - FastAPI entry point for SecInt v2 Threat Intelligence API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from routers import iocs
from routers import reports
from routers import ingestion
from database import connect_db, disconnect_db
from services.api_validator import api_validator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to MongoDB
    await connect_db()
    yield
    # Shutdown: disconnect
    await disconnect_db()

app = FastAPI(
    title="SecInt v2 - Threat Intelligence API",
    description="Real-time threat intelligence platform with IOC extraction, enrichment, and severity scoring",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(iocs.router, prefix="/api/iocs", tags=["IOCs"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["Ingestion"])

@app.get("/")
async def root():
    return {
        "message": "SecInt v2 - Real-time Threat Intelligence API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/health/apis")
async def api_health(use_cache: bool = True):
    """
    Check health status of all external threat intelligence APIs
    
    Args:
        use_cache: Use cached results if available (default True)
        
    Returns:
        Health status for all APIs
    """
    health_status = await api_validator.validate_all_apis(use_cache=use_cache)
    overall_status = api_validator.get_overall_status(health_status)
    
    return {
        "overall_status": overall_status,
        "apis": health_status,
        "last_checked": api_validator.last_check.isoformat() if api_validator.last_check else None
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
