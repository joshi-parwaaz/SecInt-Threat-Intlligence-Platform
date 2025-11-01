"""
iocs.py - API endpoints for IOC management and retrieval
SecInt v2 - Real-time threat intelligence platform
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
import csv
import io

from models import (
    IOCRecord, IOCStats, IOCSearchQuery, IOCExportRequest,
    IOCType, SeverityLevel, ThreatSource
)
from database import get_collection

router = APIRouter()

@router.get("/")
async def get_iocs(
    ioc_type: Optional[IOCType] = None,
    severity: Optional[SeverityLevel] = None,
    min_severity: Optional[int] = Query(None, ge=0, le=10),
    source: Optional[ThreatSource] = None,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Get IOCs with optional filtering
    
    Args:
        ioc_type: Filter by IOC type (ipv4, domain, hash, etc.)
        severity: Filter by severity level (exact match)
        min_severity: Filter by minimum severity score (e.g., 5 for HIGH+, 8 for CRITICAL)
        source: Filter by threat source
        limit: Maximum results to return
        offset: Pagination offset
        
    Returns:
        Dict with iocs list and total count
    """
    collection = get_collection("iocs")
    
    # Build query filter
    query_filter = {}
    if ioc_type:
        query_filter["ioc_type"] = ioc_type.value
    if severity:
        query_filter["severity"] = severity.value
    if min_severity is not None:
        query_filter["severity_score"] = {"$gte": min_severity}
    if source:
        query_filter["source"] = source.value
    
    # Get total count
    total = await collection.count_documents(query_filter)
    
    # Execute query with pagination
    cursor = collection.find(query_filter).sort("first_seen", -1).skip(offset).limit(limit)
    iocs = await cursor.to_list(length=limit)
    
    # Convert MongoDB _id to string and datetime to ISO format
    for ioc in iocs:
        if "_id" in ioc:
            ioc["_id"] = str(ioc["_id"])
        if "first_seen" in ioc and isinstance(ioc["first_seen"], datetime):
            ioc["first_seen"] = ioc["first_seen"].isoformat()
        if "last_updated" in ioc and isinstance(ioc["last_updated"], datetime):
            ioc["last_updated"] = ioc["last_updated"].isoformat()
    
    return {"iocs": iocs, "total": total}

@router.get("/critical", response_model=List[IOCRecord])
async def get_critical_iocs(limit: int = Query(50, le=200)):
    """Get CRITICAL severity IOCs"""
    collection = get_collection("iocs")
    
    cursor = collection.find({"severity": "CRITICAL"}).sort("severity_score", -1).limit(limit)
    iocs = await cursor.to_list(length=limit)
    
    for ioc in iocs:
        if "_id" in ioc:
            ioc["_id"] = str(ioc["_id"])
    
    return iocs

@router.get("/recent", response_model=List[IOCRecord])
async def get_recent_iocs(hours: int = Query(24, ge=1, le=168)):
    """
    Get IOCs discovered in the last N hours
    
    Args:
        hours: Number of hours to look back (default 24, max 168 = 1 week)
    """
    collection = get_collection("iocs")
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    cursor = collection.find({
        "first_seen": {"$gte": cutoff_time}
    }).sort("first_seen", -1).limit(100)
    
    iocs = await cursor.to_list(length=100)
    
    for ioc in iocs:
        if "_id" in ioc:
            ioc["_id"] = str(ioc["_id"])
    
    return iocs

@router.get("/search", response_model=List[IOCRecord])
async def search_iocs(
    q: str = Query(..., min_length=2),
    limit: int = Query(50, le=200)
):
    """
    Search IOCs by value or description
    
    Args:
        q: Search query string
        limit: Maximum results
    """
    collection = get_collection("iocs")
    
    # Search in ioc_value, description, and malware_family
    query_filter = {
        "$or": [
            {"ioc_value": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"malware_family": {"$regex": q, "$options": "i"}},
            {"context": {"$regex": q, "$options": "i"}}
        ]
    }
    
    cursor = collection.find(query_filter).sort("severity_score", -1).limit(limit)
    iocs = await cursor.to_list(length=limit)
    
    for ioc in iocs:
        if "_id" in ioc:
            ioc["_id"] = str(ioc["_id"])
    
    return iocs

@router.get("/stats", response_model=IOCStats)
async def get_ioc_stats():
    """Get IOC statistics and counts"""
    collection = get_collection("iocs")
    
    # Total count
    total_iocs = await collection.count_documents({})
    
    # Count by type
    type_pipeline = [
        {"$group": {"_id": "$ioc_type", "count": {"$sum": 1}}}
    ]
    by_type_cursor = collection.aggregate(type_pipeline)
    by_type = {doc["_id"]: doc["count"] async for doc in by_type_cursor}
    
    # Count by severity
    severity_pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    by_severity_cursor = collection.aggregate(severity_pipeline)
    by_severity = {doc["_id"]: doc["count"] async for doc in by_severity_cursor}
    
    # Count by source
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    by_source_cursor = collection.aggregate(source_pipeline)
    by_source = {doc["_id"]: doc["count"] async for doc in by_source_cursor}
    
    # Critical and high counts
    critical_count = by_severity.get("CRITICAL", 0)
    high_count = by_severity.get("HIGH", 0)
    
    # Recent count (last 7 days)
    cutoff_time = datetime.utcnow() - timedelta(days=7)
    recent_count = await collection.count_documents({
        "first_seen": {"$gte": cutoff_time}
    })
    
    return IOCStats(
        total_iocs=total_iocs,
        by_type=by_type,
        by_severity=by_severity,
        by_source=by_source,
        critical_count=critical_count,
        high_count=high_count,
        recent_count=recent_count
    )

@router.get("/export")
async def export_iocs(
    format: str = Query("json", regex="^(json|csv)$"),
    severity: Optional[SeverityLevel] = None,
    ioc_type: Optional[IOCType] = None,
    limit: int = Query(1000, le=5000)
):
    """
    Export IOCs to JSON or CSV format
    
    Args:
        format: Export format (json or csv)
        severity: Filter by severity
        ioc_type: Filter by IOC type
        limit: Maximum records to export
    """
    collection = get_collection("iocs")
    
    # Build filter
    query_filter = {}
    if severity:
        query_filter["severity"] = severity.value
    if ioc_type:
        query_filter["ioc_type"] = ioc_type.value
    
    # Fetch IOCs
    cursor = collection.find(query_filter).sort("severity_score", -1).limit(limit)
    iocs = await cursor.to_list(length=limit)
    
    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        if iocs:
            fieldnames = ['ioc_value', 'ioc_type', 'severity', 'severity_score', 
                         'malware_family', 'vt_detections', 'source', 'first_seen']
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for ioc in iocs:
                # Convert datetime to string
                if 'first_seen' in ioc and isinstance(ioc['first_seen'], datetime):
                    ioc['first_seen'] = ioc['first_seen'].isoformat()
                writer.writerow(ioc)
        
        from fastapi.responses import StreamingResponse
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=iocs_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    else:
        # Return JSON
        for ioc in iocs:
            if "_id" in ioc:
                ioc["_id"] = str(ioc["_id"])
            # Convert datetime to string
            if 'first_seen' in ioc and isinstance(ioc['first_seen'], datetime):
                ioc['first_seen'] = ioc['first_seen'].isoformat()
        
        return iocs

@router.get("/{ioc_value}")
async def get_ioc_details(ioc_value: str):
    """
    Get detailed information about a specific IOC
    
    Args:
        ioc_value: The IOC value to look up
    """
    collection = get_collection("iocs")
    
    ioc = await collection.find_one({"ioc_value": ioc_value})
    
    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")
    
    if "_id" in ioc:
        ioc["_id"] = str(ioc["_id"])
    
    return ioc
