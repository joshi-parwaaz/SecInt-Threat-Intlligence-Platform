"""
reports.py - Report generation API endpoints
Provides endpoints for generating and downloading threat intelligence reports
"""
from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import Optional, List
from datetime import datetime
import io
import logging

from database import get_db_client
from services.report_generator import create_report_generator
from models import SeverityLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary")
async def get_report_summary():
    """
    Get executive summary for threat intelligence report
    
    Returns:
        Executive summary with key metrics
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        summary = await generator.generate_executive_summary()
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-threats")
async def get_top_threats(limit: int = Query(20, ge=1, le=100)):
    """
    Get top threats by severity score
    
    Args:
        limit: Number of threats to return (default 20, max 100)
        
    Returns:
        List of top threat IOCs
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        threats = await generator.get_top_threats(limit=limit)
        
        return {
            "success": True,
            "count": len(threats),
            "data": threats
        }
    except Exception as e:
        logger.error(f"Failed to get top threats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocklist")
async def get_actionable_blocklist(
    severity: Optional[List[SeverityLevel]] = Query(None)
):
    """
    Get actionable blocklist for firewall/SIEM integration
    
    Args:
        severity: Filter by severity levels (default: CRITICAL, HIGH)
        
    Returns:
        Dictionary with IPs, domains, URLs, and hashes to block
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        
        severity_filter = None
        if severity:
            severity_filter = [s.value for s in severity]
        
        blocklist = await generator.get_actionable_blocklist(severity_filter)
        
        # Calculate totals
        total_ips = len(blocklist['ipv4_addresses'])
        total_domains = len(blocklist['domains'])
        total_urls = len(blocklist['urls'])
        total_hashes = sum(len(v) for v in blocklist['file_hashes'].values())
        
        return {
            "success": True,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "severity_filter": severity_filter or ['CRITICAL', 'HIGH'],
                "totals": {
                    "ips": total_ips,
                    "domains": total_domains,
                    "urls": total_urls,
                    "hashes": total_hashes
                }
            },
            "data": blocklist
        }
    except Exception as e:
        logger.error(f"Failed to generate blocklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/csv")
async def download_csv_report(
    severity: Optional[List[SeverityLevel]] = Query(None),
    limit: int = Query(1000, ge=1, le=10000)
):
    """
    Download threat intelligence report in CSV format
    
    Args:
        severity: Filter by severity levels
        limit: Maximum records (default 1000, max 10000)
        
    Returns:
        CSV file download
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        
        severity_filter = None
        if severity:
            severity_filter = [s.value for s in severity]
        
        csv_content = await generator.generate_csv_report(severity_filter, limit)
        
        # Create streaming response
        output = io.BytesIO(csv_content.encode('utf-8'))
        
        filename = f"secint_threats_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate CSV report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/json")
async def download_json_report(include_summary: bool = Query(True)):
    """
    Download threat intelligence report in JSON format
    
    Args:
        include_summary: Include executive summary (default True)
        
    Returns:
        JSON file download
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        
        report_data = await generator.generate_json_report(include_summary)
        
        filename = f"secint_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        return Response(
            content=str(report_data).encode('utf-8'),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate JSON report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/html", response_class=HTMLResponse)
async def download_html_report():
    """
    Download threat intelligence report in HTML format
    
    Returns:
        HTML report for viewing in browser
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        
        html_content = await generator.generate_html_report()
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/cef")
async def export_cef_format(
    severity: Optional[List[SeverityLevel]] = Query(None),
    limit: int = Query(500, ge=1, le=5000)
):
    """
    Export IOCs in Common Event Format (CEF) for SIEM integration
    
    Args:
        severity: Filter by severity levels
        limit: Maximum events (default 500, max 5000)
        
    Returns:
        CEF formatted events
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        
        severity_filter = None
        if severity:
            severity_filter = [s.value for s in severity]
        
        cef_content = await generator.generate_cef_format(severity_filter, limit)
        
        filename = f"secint_cef_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return Response(
            content=cef_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate CEF format: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/syslog")
async def export_syslog_format(
    severity: Optional[List[SeverityLevel]] = Query(None),
    limit: int = Query(500, ge=1, le=5000)
):
    """
    Export IOCs in Syslog format for generic SIEM integration
    
    Args:
        severity: Filter by severity levels
        limit: Maximum events (default 500, max 5000)
        
    Returns:
        Syslog formatted events
    """
    try:
        db_client = get_db_client()
        generator = create_report_generator(db_client)
        
        severity_filter = None
        if severity:
            severity_filter = [s.value for s in severity]
        
        syslog_content = await generator.generate_syslog_format(severity_filter, limit)
        
        filename = f"secint_syslog_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        
        return Response(
            content=syslog_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate Syslog format: {e}")
        raise HTTPException(status_code=500, detail=str(e))
