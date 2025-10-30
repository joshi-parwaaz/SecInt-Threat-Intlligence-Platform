"""
routers/threats.py - Threat data endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models import ThreatRecord, ThreatType, DatasetSource
from database import get_collection
from bson import ObjectId

router = APIRouter()

@router.get("/", response_model=List[ThreatRecord])
async def get_threats(
    limit: int = Query(100, ge=1, le=1000),
    threat_type: Optional[ThreatType] = None,
    dataset: Optional[DatasetSource] = None
):
    """Get threats with optional filters"""
    collection = get_collection("threats")
    
    query = {}
    if threat_type:
        query["threat_type"] = threat_type.value
    if dataset:
        query["dataset"] = dataset.value
    
    cursor = collection.find(query).limit(limit).sort("timestamp", -1)
    threats = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for threat in threats:
        threat["_id"] = str(threat["_id"])
    
    return threats

@router.get("/{threat_id}", response_model=ThreatRecord)
async def get_threat_by_id(threat_id: str):
    """Get a specific threat by ID"""
    collection = get_collection("threats")
    
    try:
        threat = await collection.find_one({"_id": ObjectId(threat_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid threat ID format")
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    threat["_id"] = str(threat["_id"])
    return threat

@router.get("/search/content")
async def search_threats(
    q: str = Query(..., min_length=3),
    limit: int = Query(50, ge=1, le=500)
):
    """Search threats by content (text search)"""
    collection = get_collection("threats")
    
    # Simple text search (requires text index on 'content' field)
    threats = await collection.find(
        {"$text": {"$search": q}}
    ).limit(limit).to_list(length=limit)
    
    for threat in threats:
        threat["_id"] = str(threat["_id"])
    
    return threats
