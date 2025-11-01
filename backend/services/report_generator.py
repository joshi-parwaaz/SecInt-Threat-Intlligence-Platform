"""
report_generator.py - Threat Intelligence Report Generation Service
Generates exportable reports in CSV, JSON, and HTML formats for SOC teams
"""
import csv
import json
import io
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate threat intelligence reports in multiple formats"""
    
    def __init__(self, db_client: AsyncIOMotorClient, db_name: str = "secint"):
        """
        Initialize report generator
        
        Args:
            db_client: MongoDB async client
            db_name: Database name
        """
        self.db = db_client[db_name]
        self.iocs_collection = self.db['iocs']
    
    async def generate_executive_summary(self) -> Dict:
        """
        Generate executive summary statistics
        
        Returns:
            Dictionary with key metrics
        """
        # Total IOCs
        total_iocs = await self.iocs_collection.count_documents({})
        
        # Critical and High severity counts
        critical_count = await self.iocs_collection.count_documents({'severity': 'CRITICAL'})
        high_count = await self.iocs_collection.count_documents({'severity': 'HIGH'})
        medium_count = await self.iocs_collection.count_documents({'severity': 'MEDIUM'})
        low_count = await self.iocs_collection.count_documents({'severity': 'LOW'})
        
        # Recent threats (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_count = await self.iocs_collection.count_documents({
            'first_seen': {'$gte': cutoff_time}
        })
        
        # Top malware families
        malware_pipeline = [
            {'$match': {'malware_family': {'$ne': None, '$exists': True}}},
            {'$group': {'_id': '$malware_family', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        malware_cursor = self.iocs_collection.aggregate(malware_pipeline)
        top_malware = [{'family': doc['_id'], 'count': doc['count']} async for doc in malware_cursor]
        
        # IOC type distribution
        type_pipeline = [
            {'$group': {'_id': '$ioc_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        type_cursor = self.iocs_collection.aggregate(type_pipeline)
        ioc_types = {doc['_id']: doc['count'] async for doc in type_cursor}
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'total_iocs': total_iocs,
            'severity_distribution': {
                'CRITICAL': critical_count,
                'HIGH': high_count,
                'MEDIUM': medium_count,
                'LOW': low_count
            },
            'recent_threats_24h': recent_count,
            'top_malware_families': top_malware,
            'ioc_type_distribution': ioc_types,
            'threat_score': self._calculate_threat_score(critical_count, high_count, recent_count)
        }
    
    def _calculate_threat_score(self, critical: int, high: int, recent: int) -> str:
        """
        Calculate overall threat level
        
        Args:
            critical: Number of critical threats
            high: Number of high threats
            recent: Number of recent threats
            
        Returns:
            Threat level string
        """
        score = (critical * 3) + (high * 2) + recent
        
        if score > 100:
            return "SEVERE"
        elif score > 50:
            return "ELEVATED"
        elif score > 20:
            return "MODERATE"
        else:
            return "LOW"
    
    async def get_top_threats(self, limit: int = 20) -> List[Dict]:
        """
        Get top threats by severity score
        
        Args:
            limit: Number of threats to return
            
        Returns:
            List of top threat IOCs
        """
        cursor = self.iocs_collection.find(
            {},
            {
                'ioc_value': 1,
                'ioc_type': 1,
                'severity': 1,
                'severity_score': 1,
                'malware_family': 1,
                'vt_detections': 1,
                'abuse_score': 1,
                'first_seen': 1,
                '_id': 0
            }
        ).sort('severity_score', -1).limit(limit)
        
        threats = await cursor.to_list(length=limit)
        
        # Convert datetime to string
        for threat in threats:
            if 'first_seen' in threat and isinstance(threat['first_seen'], datetime):
                threat['first_seen'] = threat['first_seen'].isoformat()
        
        return threats
    
    async def get_actionable_blocklist(self, severity_filter: List[str] = None) -> Dict[str, List[str]]:
        """
        Get actionable blocklist for firewall/SIEM integration
        
        Args:
            severity_filter: List of severity levels to include (default: CRITICAL, HIGH)
            
        Returns:
            Dictionary with IPs, domains, and URLs to block
        """
        if severity_filter is None:
            severity_filter = ['CRITICAL', 'HIGH']
        
        # Query for high-priority IOCs
        query = {'severity': {'$in': severity_filter}}
        
        # Aggregate by IOC type
        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$ioc_type',
                'values': {'$addToSet': '$ioc_value'}
            }}
        ]
        
        cursor = self.iocs_collection.aggregate(pipeline)
        results = {doc['_id']: doc['values'] async for doc in cursor}
        
        # Organize by category
        blocklist = {
            'ipv4_addresses': results.get('ipv4', []),
            'domains': results.get('domain', []),
            'urls': results.get('url', []),
            'file_hashes': {
                'md5': results.get('md5', []),
                'sha1': results.get('sha1', []),
                'sha256': results.get('sha256', [])
            }
        }
        
        logger.info(f"✅ Generated blocklist: {len(blocklist['ipv4_addresses'])} IPs, "
                   f"{len(blocklist['domains'])} domains, {len(blocklist['urls'])} URLs")
        
        return blocklist
    
    async def generate_csv_report(self, severity_filter: List[str] = None, limit: int = 1000) -> str:
        """
        Generate CSV format report
        
        Args:
            severity_filter: Filter by severity levels
            limit: Maximum records
            
        Returns:
            CSV string
        """
        query = {}
        if severity_filter:
            query['severity'] = {'$in': severity_filter}
        
        cursor = self.iocs_collection.find(query).sort('severity_score', -1).limit(limit)
        iocs = await cursor.to_list(length=limit)
        
        # Generate CSV
        output = io.StringIO()
        fieldnames = [
            'ioc_value', 'ioc_type', 'severity', 'severity_score',
            'malware_family', 'vt_detections', 'abuse_score',
            'source', 'first_seen', 'description'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for ioc in iocs:
            # Convert datetime to string
            if 'first_seen' in ioc and isinstance(ioc['first_seen'], datetime):
                ioc['first_seen'] = ioc['first_seen'].isoformat()
            writer.writerow(ioc)
        
        return output.getvalue()
    
    async def generate_json_report(self, include_summary: bool = True) -> Dict:
        """
        Generate JSON format report
        
        Args:
            include_summary: Include executive summary
            
        Returns:
            JSON-serializable dictionary
        """
        report = {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'report_type': 'threat_intelligence',
                'version': '2.0'
            }
        }
        
        if include_summary:
            report['executive_summary'] = await self.generate_executive_summary()
        
        # Top threats
        report['top_threats'] = await self.get_top_threats(limit=50)
        
        # Actionable blocklist
        report['actionable_blocklist'] = await self.get_actionable_blocklist()
        
        return report
    
    async def generate_html_report(self) -> str:
        """
        Generate HTML format report for viewing in browser
        
        Returns:
            HTML string
        """
        summary = await self.generate_executive_summary()
        top_threats = await self.get_top_threats(limit=20)
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecInt v2 - Threat Intelligence Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #2a2a2a;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #4CAF50;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2196F3;
            margin-top: 30px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #3a3a3a;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .metric-card.critical {{ border-left-color: #f44336; }}
        .metric-card.high {{ border-left-color: #ff9800; }}
        .metric-card.medium {{ border-left-color: #ffc107; }}
        .metric-card.low {{ border-left-color: #4CAF50; }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 14px;
            color: #999;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #3a3a3a;
        }}
        th {{
            background: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #555;
        }}
        tr:hover {{
            background: #444;
        }}
        .severity-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .severity-CRITICAL {{ background: #f44336; color: white; }}
        .severity-HIGH {{ background: #ff9800; color: white; }}
        .severity-MEDIUM {{ background: #ffc107; color: black; }}
        .severity-LOW {{ background: #4CAF50; color: white; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #555;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ SecInt v2 - Threat Intelligence Report</h1>
        <p><strong>Generated:</strong> {summary['generated_at']}</p>
        <p><strong>Overall Threat Level:</strong> <span style="color: #f44336; font-weight: bold;">{summary['threat_score']}</span></p>
        
        <h2>📊 Executive Summary</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Total IOCs</div>
                <div class="metric-value">{summary['total_iocs']:,}</div>
            </div>
            <div class="metric-card critical">
                <div class="metric-label">Critical Threats</div>
                <div class="metric-value">{summary['severity_distribution']['CRITICAL']:,}</div>
            </div>
            <div class="metric-card high">
                <div class="metric-label">High Severity</div>
                <div class="metric-value">{summary['severity_distribution']['HIGH']:,}</div>
            </div>
            <div class="metric-card medium">
                <div class="metric-label">Medium Severity</div>
                <div class="metric-value">{summary['severity_distribution']['MEDIUM']:,}</div>
            </div>
            <div class="metric-card low">
                <div class="metric-label">Low Severity</div>
                <div class="metric-value">{summary['severity_distribution']['LOW']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Recent Threats (24h)</div>
                <div class="metric-value">{summary['recent_threats_24h']:,}</div>
            </div>
        </div>
        
        <h2>🦠 Top Malware Families</h2>
        <table>
            <thead>
                <tr>
                    <th>Malware Family</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'<tr><td>{m["family"]}</td><td>{m["count"]}</td></tr>' for m in summary['top_malware_families'][:10]])}
            </tbody>
        </table>
        
        <h2>🚨 Top 20 Threats to Investigate</h2>
        <table>
            <thead>
                <tr>
                    <th>IOC Value</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Score</th>
                    <th>Malware Family</th>
                    <th>VT Detections</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''<tr>
                    <td><code>{t.get('ioc_value', 'N/A')}</code></td>
                    <td>{t.get('ioc_type', 'N/A')}</td>
                    <td><span class="severity-badge severity-{t.get('severity', 'LOW')}">{t.get('severity', 'N/A')}</span></td>
                    <td>{t.get('severity_score', 0)}</td>
                    <td>{t.get('malware_family', 'Unknown')}</td>
                    <td>{t.get('vt_detections', 'N/A')}</td>
                </tr>''' for t in top_threats])}
            </tbody>
        </table>
        
        <div class="footer">
            <p>SecInt v2 - Real-Time Threat Intelligence Platform | Generated by Report Generator Service</p>
            <p>⚠️ This report contains sensitive threat intelligence data. Handle according to your organization's security policies.</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    async def generate_cef_format(self, severity_filter: List[str] = None, limit: int = 500) -> str:
        """
        Generate Common Event Format (CEF) for SIEM integration
        
        Args:
            severity_filter: Filter by severity
            limit: Maximum events
            
        Returns:
            CEF formatted string
        """
        query = {}
        if severity_filter:
            query['severity'] = {'$in': severity_filter}
        
        cursor = self.iocs_collection.find(query).sort('severity_score', -1).limit(limit)
        iocs = await cursor.to_list(length=limit)
        
        cef_events = []
        for ioc in iocs:
            # CEF Format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
            timestamp = ioc.get('first_seen', datetime.utcnow())
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%b %d %Y %H:%M:%S')
            
            severity_map = {'CRITICAL': 10, 'HIGH': 7, 'MEDIUM': 5, 'LOW': 3, 'UNKNOWN': 1}
            cef_severity = severity_map.get(ioc.get('severity', 'UNKNOWN'), 1)
            
            cef_line = (
                f"CEF:0|SecInt|ThreatIntel|2.0|{ioc.get('ioc_type', 'unknown')}|"
                f"Threat Indicator Detected|{cef_severity}|"
                f"src={ioc.get('ioc_value', 'unknown')} "
                f"msg={ioc.get('malware_family', 'Unknown threat')} "
                f"cs1Label=Severity cs1={ioc.get('severity', 'UNKNOWN')} "
                f"cs2Label=VTDetections cs2={ioc.get('vt_detections', 'N/A')} "
                f"cn1Label=SeverityScore cn1={ioc.get('severity_score', 0)} "
                f"rt={timestamp}"
            )
            cef_events.append(cef_line)
        
        return '\n'.join(cef_events)
    
    async def generate_syslog_format(self, severity_filter: List[str] = None, limit: int = 500) -> str:
        """
        Generate Syslog format for generic SIEM integration
        
        Args:
            severity_filter: Filter by severity
            limit: Maximum events
            
        Returns:
            Syslog formatted string
        """
        query = {}
        if severity_filter:
            query['severity'] = {'$in': severity_filter}
        
        cursor = self.iocs_collection.find(query).sort('severity_score', -1).limit(limit)
        iocs = await cursor.to_list(length=limit)
        
        syslog_events = []
        for ioc in iocs:
            timestamp = ioc.get('first_seen', datetime.utcnow())
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
            
            # RFC 5424 format
            syslog_line = (
                f"<134>1 {timestamp} secint-v2 threat-intel - - - "
                f"ioc_value=\"{ioc.get('ioc_value', 'unknown')}\" "
                f"ioc_type=\"{ioc.get('ioc_type', 'unknown')}\" "
                f"severity=\"{ioc.get('severity', 'UNKNOWN')}\" "
                f"severity_score={ioc.get('severity_score', 0)} "
                f"malware_family=\"{ioc.get('malware_family', 'Unknown')}\" "
                f"vt_detections=\"{ioc.get('vt_detections', 'N/A')}\""
            )
            syslog_events.append(syslog_line)
        
        return '\n'.join(syslog_events)


# Factory function for creating report generator instance
def create_report_generator(db_client: AsyncIOMotorClient, db_name: str = "secint") -> ReportGenerator:
    """
    Create a report generator instance
    
    Args:
        db_client: MongoDB async client
        db_name: Database name
        
    Returns:
        ReportGenerator instance
    """
    return ReportGenerator(db_client, db_name)
