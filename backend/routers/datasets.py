"""
routers/datasets.py - Dataset management and status endpoints
"""
from fastapi import APIRouter
from models import IngestionLog
from database import get_collection
from typing import List

router = APIRouter()

@router.get("/status")
async def get_dataset_status():
    """Get ingestion status for all datasets"""
    threats_col = get_collection("threats")
    
    # Aggregate threat counts by dataset
    pipeline = [
        {"$group": {
            "_id": "$dataset",
            "total_threats": {"$sum": 1},
            "threat_types": {"$addToSet": "$threat_type"},
            "latest_timestamp": {"$max": "$timestamp"}
        }},
        {"$project": {
            "dataset": "$_id",
            "total_threats": 1,
            "unique_threat_types": {"$size": "$threat_types"},
            "latest_update": "$latest_timestamp",
            "_id": 0
        }},
        {"$sort": {"total_threats": -1}}
    ]
    
    datasets = await threats_col.aggregate(pipeline).to_list(length=None)
    
    return {"datasets": datasets}

@router.get("/logs", response_model=List[IngestionLog])
async def get_ingestion_logs(limit: int = 50):
    """Get recent ingestion logs"""
    logs_col = get_collection("ingestion_logs")
    
    logs = await logs_col.find().sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    for log in logs:
        log["_id"] = str(log["_id"])
    
    return logs
