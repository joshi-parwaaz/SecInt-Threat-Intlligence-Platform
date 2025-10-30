"""
main.py - FastAPI entry point for Dark Web Threat Intelligence API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from routers import threats, analytics, datasets
from database import connect_db, disconnect_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to MongoDB
    await connect_db()
    yield
    # Shutdown: disconnect
    await disconnect_db()

app = FastAPI(
    title="Dark Web Threat Intelligence API",
    description="Backend API for threat intelligence ingestion, classification, and analytics",
    version="1.0.0",
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
app.include_router(threats.router, prefix="/api/threats", tags=["Threats"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])

@app.get("/")
async def root():
    return {
        "message": "Dark Web Threat Intel API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
