"""
routers/analytics.py - Analytics and aggregation endpoints
"""
from fastapi import APIRouter
from models import AnalyticsSummary, ThreatRecord
from database import get_collection
from datetime import datetime

router = APIRouter()

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary():
    """Get overall analytics summary"""
    threats_col = get_collection("threats")
    
    # Total count
    total = await threats_col.count_documents({})
    
    # Group by threat type
    pipeline_type = [
        {"$group": {"_id": "$threat_type", "count": {"$sum": 1}}}
    ]
    type_agg = await threats_col.aggregate(pipeline_type).to_list(length=None)
    threats_by_type = {item["_id"]: item["count"] for item in type_agg}
    
    # Group by dataset
    pipeline_dataset = [
        {"$group": {"_id": "$dataset", "count": {"$sum": 1}}}
    ]
    dataset_agg = await threats_col.aggregate(pipeline_dataset).to_list(length=None)
    threats_by_dataset = {item["_id"]: item["count"] for item in dataset_agg}
    
    # Recent threats
    recent = await threats_col.find().sort("timestamp", -1).limit(10).to_list(length=10)
    for r in recent:
        r["_id"] = str(r["_id"])
    
    return AnalyticsSummary(
        total_threats=total,
        threats_by_type=threats_by_type,
        threats_by_dataset=threats_by_dataset,
        recent_threats=recent
    )

@router.get("/trends")
async def get_trends():
    """Get time-series trends (daily counts)"""
    threats_col = get_collection("threats")
    
    pipeline = [
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}},
        {"$limit": 30}
    ]
    
    trends = await threats_col.aggregate(pipeline).to_list(length=30)
    return {"trends": trends}
