"""
report_generator.py - Threat Intelligence Report Generation Service

Performance fixes vs original:
  - generate_executive_summary: was 6 round-trips → now 1 $facet pipeline
  - get_top_threats: uses projection to avoid pulling full documents
  - get_actionable_blocklist: single pass with $group instead of 4 separate queries
"""
import csv
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

_BLOCKLIST_SEVERITIES = ["CRITICAL", "HIGH"]

# Minimal projection for list/export queries
_EXPORT_PROJECTION = {
    "_id": 0,
    "ioc_value": 1,
    "ioc_type": 1,
    "severity": 1,
    "severity_score": 1,
    "malware_family": 1,
    "threat_type": 1,
    "source": 1,
    "vt_detections": 1,
    "abuse_score": 1,
    "description": 1,
    "first_seen": 1,
    "last_updated": 1,
    "tags": 1,
    "threat_actor": 1,
}


def _fmt_dt(val) -> Optional[str]:
    if isinstance(val, datetime):
        return val.isoformat()
    return val


class ReportGenerator:
    def __init__(self, db_client: AsyncIOMotorClient, db_name: str = "secint"):
        self.db = db_client[db_name]
        self.col = self.db["iocs"]

    # ------------------------------------------------------------------
    # Executive summary — single $facet pipeline
    # ------------------------------------------------------------------
    async def generate_executive_summary(self) -> Dict:
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)

        pipeline = [
            {
                "$facet": {
                    "by_severity": [
                        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
                    ],
                    "by_type": [
                        {"$group": {"_id": "$ioc_type", "count": {"$sum": 1}}}
                    ],
                    "by_source": [
                        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
                    ],
                    "total": [{"$count": "n"}],
                    "recent_24h": [
                        {"$match": {"first_seen": {"$gte": cutoff_24h}}},
                        {"$count": "n"},
                    ],
                    "top_malware": [
                        {"$match": {"malware_family": {"$ne": None, "$exists": True}}},
                        {"$group": {"_id": "$malware_family", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 10},
                    ],
                    "top_threats": [
                        {"$sort": {"severity_score": -1}},
                        {"$limit": 5},
                        {"$project": {
                            "_id": 0,
                            "ioc_value": 1,
                            "ioc_type": 1,
                            "severity": 1,
                            "severity_score": 1,
                            "malware_family": 1,
                            "source": 1,
                        }},
                    ],
                }
            }
        ]

        result = await self.col.aggregate(pipeline).to_list(length=1)
        if not result:
            return {"generated_at": datetime.now(timezone.utc).isoformat(), "total_iocs": 0}

        f = result[0]
        by_sev    = {d["_id"]: d["count"] for d in f.get("by_severity", []) if d["_id"]}
        by_type   = {d["_id"]: d["count"] for d in f.get("by_type", [])     if d["_id"]}
        by_source = {d["_id"]: d["count"] for d in f.get("by_source", [])   if d["_id"]}
        total     = f["total"][0]["n"]     if f.get("total")     else 0
        recent    = f["recent_24h"][0]["n"] if f.get("recent_24h") else 0

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_iocs": total,
            "severity_distribution": {
                "CRITICAL": by_sev.get("CRITICAL", 0),
                "HIGH":     by_sev.get("HIGH",     0),
                "MEDIUM":   by_sev.get("MEDIUM",   0),
                "LOW":      by_sev.get("LOW",       0),
            },
            "recent_threats_24h": recent,
            "ioc_type_distribution": by_type,
            "source_distribution": by_source,
            "top_malware_families": [
                {"family": d["_id"], "count": d["count"]}
                for d in f.get("top_malware", [])
            ],
            "top_threats": f.get("top_threats", []),
        }

    # ------------------------------------------------------------------
    # Top threats — index-covered sort + projection
    # ------------------------------------------------------------------
    async def get_top_threats(self, limit: int = 20) -> List[Dict]:
        cursor = (
            self.col.find({}, _EXPORT_PROJECTION)
            .sort("severity_score", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        for d in docs:
            d["first_seen"]   = _fmt_dt(d.get("first_seen"))
            d["last_updated"] = _fmt_dt(d.get("last_updated"))
        return docs

    # ------------------------------------------------------------------
    # Actionable blocklist — single pass with $group by type
    # ------------------------------------------------------------------
    async def get_actionable_blocklist(
        self, severity_filter: Optional[List[str]] = None
    ) -> Dict:
        severities = severity_filter or _BLOCKLIST_SEVERITIES
        query = {"severity": {"$in": severities}}
        projection = {"_id": 0, "ioc_value": 1, "ioc_type": 1, "severity_score": 1}

        cursor = (
            self.col.find(query, projection)
            .sort("severity_score", -1)
            .limit(5000)
        )
        docs = await cursor.to_list(length=5000)

        blocklist: Dict = {
            "ipv4_addresses": [],
            "domains": [],
            "urls": [],
            "file_hashes": {"md5": [], "sha256": [], "sha1": []},
            "email_addresses": [],
            "cves": [],
        }

        for d in docs:
            t   = d.get("ioc_type", "")
            val = d.get("ioc_value", "")
            if t == "ipv4":
                blocklist["ipv4_addresses"].append(val)
            elif t == "domain":
                blocklist["domains"].append(val)
            elif t == "url":
                blocklist["urls"].append(val)
            elif t in ("md5", "sha256", "sha1"):
                blocklist["file_hashes"].setdefault(t, []).append(val)
            elif t == "email":
                blocklist["email_addresses"].append(val)
            elif t == "cve":
                blocklist["cves"].append(val)

        return blocklist

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------
    async def generate_csv_report(
        self,
        severity_filter: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> str:
        query = {"severity": {"$in": severity_filter}} if severity_filter else {}
        cursor = (
            self.col.find(query, _EXPORT_PROJECTION)
            .sort("severity_score", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)

        fieldnames = [
            "ioc_value", "ioc_type", "severity", "severity_score",
            "malware_family", "threat_type", "source", "vt_detections",
            "abuse_score", "description", "first_seen", "last_updated",
            "tags", "threat_actor",
        ]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for d in docs:
            d["first_seen"]   = _fmt_dt(d.get("first_seen"))
            d["last_updated"] = _fmt_dt(d.get("last_updated"))
            if isinstance(d.get("tags"), list):
                d["tags"] = ", ".join(d["tags"])
            writer.writerow(d)

        return output.getvalue()

    # ------------------------------------------------------------------
    # JSON export
    # ------------------------------------------------------------------
    async def generate_json_report(self, include_summary: bool = True) -> str:
        report: Dict = {"generated_at": datetime.now(timezone.utc).isoformat()}

        if include_summary:
            report["summary"] = await self.generate_executive_summary()

        cursor = (
            self.col.find({}, _EXPORT_PROJECTION)
            .sort("severity_score", -1)
            .limit(5000)
        )
        docs = await cursor.to_list(length=5000)
        for d in docs:
            d["first_seen"]   = _fmt_dt(d.get("first_seen"))
            d["last_updated"] = _fmt_dt(d.get("last_updated"))

        report["iocs"] = docs
        return json.dumps(report, default=str, indent=2)

    # ------------------------------------------------------------------
    # HTML report
    # ------------------------------------------------------------------
    async def generate_html_report(self) -> str:
        summary = await self.generate_executive_summary()
        threats = await self.get_top_threats(limit=50)

        rows = ""
        for t in threats:
            sev   = t.get("severity", "")
            color = {"CRITICAL": "#ef4444", "HIGH": "#f97316",
                     "MEDIUM": "#eab308", "LOW": "#22c55e"}.get(sev, "#6b7280")
            rows += (
                f"<tr>"
                f"<td style='font-family:monospace;font-size:12px'>{t.get('ioc_value','')}</td>"
                f"<td>{t.get('ioc_type','')}</td>"
                f"<td style='color:{color};font-weight:bold'>{sev}</td>"
                f"<td>{t.get('severity_score','')}</td>"
                f"<td>{t.get('malware_family') or '—'}</td>"
                f"<td>{t.get('source','')}</td>"
                f"</tr>"
            )

        sev_dist = summary.get("severity_distribution", {})
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SecInt Threat Intelligence Report</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 32px; }}
    h1   {{ color: #eab308; font-size: 28px; margin-bottom: 4px; }}
    .sub {{ color: #64748b; margin-bottom: 32px; font-size: 14px; }}
    .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 32px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px 28px; min-width: 140px; }}
    .card .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
    .card .value {{ font-size: 32px; font-weight: 700; color: #f1f5f9; margin-top: 4px; }}
    .card.crit .value {{ color: #ef4444; }}
    .card.high .value {{ color: #f97316; }}
    table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
    th    {{ background: #334155; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; padding: 12px 16px; text-align: left; }}
    td    {{ padding: 10px 16px; border-bottom: 1px solid #1e293b; font-size: 13px; color: #cbd5e1; }}
    tr:nth-child(even) td {{ background: #0f172a22; }}
  </style>
</head>
<body>
  <h1>🛡️ SecInt Threat Intelligence Report</h1>
  <p class="sub">Generated: {summary.get('generated_at','')} &nbsp;|&nbsp; Total IOCs: {summary.get('total_iocs', 0)}</p>
  <div class="cards">
    <div class="card crit"><div class="label">Critical</div><div class="value">{sev_dist.get('CRITICAL',0)}</div></div>
    <div class="card high"><div class="label">High</div><div class="value">{sev_dist.get('HIGH',0)}</div></div>
    <div class="card"><div class="label">Medium</div><div class="value">{sev_dist.get('MEDIUM',0)}</div></div>
    <div class="card"><div class="label">Low</div><div class="value">{sev_dist.get('LOW',0)}</div></div>
    <div class="card"><div class="label">Last 24h</div><div class="value">{summary.get('recent_threats_24h',0)}</div></div>
  </div>
  <table>
    <thead><tr>
      <th>IOC Value</th><th>Type</th><th>Severity</th>
      <th>Score</th><th>Malware Family</th><th>Source</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""

    # ------------------------------------------------------------------
    # CEF / Syslog export (unchanged — just use projection)
    # ------------------------------------------------------------------
    async def generate_cef_format(
        self, severity_filter: Optional[List[str]] = None, limit: int = 500
    ) -> bytes:
        query = {"severity": {"$in": severity_filter}} if severity_filter else {}
        cursor = (
            self.col.find(query, _EXPORT_PROJECTION)
            .sort("severity_score", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)

        severity_map = {"CRITICAL": "10", "HIGH": "7", "MEDIUM": "5", "LOW": "2"}
        lines = []
        for d in docs:
            sev_num = severity_map.get(d.get("severity", ""), "5")
            lines.append(
                f"CEF:0|SecInt|ThreatIntelligence|2.0|{d.get('ioc_type','unknown')}|"
                f"{d.get('malware_family') or 'Unknown Threat'}|{sev_num}|"
                f"ioc_value={d.get('ioc_value','')} "
                f"severity={d.get('severity','')} "
                f"source={d.get('source','')} "
                f"score={d.get('severity_score','')}"
            )
        return "\n".join(lines).encode("utf-8")

    async def generate_syslog_format(
        self, severity_filter: Optional[List[str]] = None, limit: int = 500
    ) -> bytes:
        query = {"severity": {"$in": severity_filter}} if severity_filter else {}
        cursor = (
            self.col.find(query, _EXPORT_PROJECTION)
            .sort("severity_score", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)

        lines = []
        now = datetime.now(timezone.utc).strftime("%b %d %H:%M:%S")
        for d in docs:
            lines.append(
                f"{now} secint threat_intel: "
                f"ioc={d.get('ioc_value','')} "
                f"type={d.get('ioc_type','')} "
                f"severity={d.get('severity','')} "
                f"score={d.get('severity_score','')} "
                f"source={d.get('source','')} "
                f"malware={d.get('malware_family') or 'unknown'}"
            )
        return "\n".join(lines).encode("utf-8")


def create_report_generator(db_client: AsyncIOMotorClient) -> ReportGenerator:
    return ReportGenerator(db_client)
