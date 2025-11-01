# SecInt v2 — Technical Documentation

A deep dive into the architecture, libraries, data models, ranking system, and operations powering the SecInt v2 Threat Intelligence Platform.

---

## Table of Contents
- Overview
- Architecture & Data Flow
- Tech Stack and Library Rationale
  - Backend (Python)
  - Frontend (React)
  - Tooling & Dev Experience
- Data Models and Schemas
- Ranking System (Severity Scorer) — Detailed Specification
- Reporting & SIEM Export
- API Endpoints (Summary)
- Scripts and How They Work
- Configuration & Environment
- Operational Considerations
- Security & Ethics

---

## Overview
SecInt v2 aggregates Indicators of Compromise (IOCs) from multiple sources (AlienVault OTX, URLhaus, etc.), enriches them with reputation and malware intelligence (VirusTotal, AbuseIPDB), computes a severity score (rule-based), stores everything in MongoDB, and exposes the data via a FastAPI backend and a modern React dashboard.

---

## Architecture & Data Flow

```mermaid
flowchart TD
  subgraph Feeds[External Threat Feeds]
    OTX[AlienVault OTX]
    URLH[URLhaus]
    VT[VirusTotal]
    ABIP[AbuseIPDB]
  end

  OTX --> ING[Direct Ingestion Service\nservices/direct_ingest.py]
  URLH --> ING

  ING --> ENR[IOC Enricher\nservices/enricher.py]
  VT --> ENR
  ABIP --> ENR

  ENR --> SC[Severity Scorer\nservices/severity_scorer.py]
  SC --> DB[(MongoDB iocs collection)]

  DB --> IOCAPI[/FastAPI Router\n/api/iocs/*/]
  DB --> RPTAPI[/FastAPI Router\n/api/reports/*/]

  RPTAPI --> RG[Report Generator\nservices/report_generator.py\nCSV | JSON | HTML | CEF | Syslog]
  IOCAPI --> FE[React Dashboard (Frontend)]
  RPTAPI --> FE

  AV[API Validator\nservices/api_validator.py\n/health/apis] -.-> IOCAPI
  AV -.-> RPTAPI
```

---

## Tech Stack and Library Rationale

### Backend (Python)
- FastAPI (fastapi): High-performance web framework with type-first design and built-in OpenAPI docs.
- Uvicorn (uvicorn[standard]): ASGI server, fast reload for development.
- Aiohttp (aiohttp): Async HTTP client for non-blocking calls to external feeds/APIs (OTX, URLhaus, VirusTotal, AbuseIPDB).
- Motor + PyMongo (motor, pymongo): Async MongoDB driver for scalable I/O.
- Pydantic v2 (pydantic, pydantic-settings): Data validation for models and settings.
- Pandas (pandas): Lightweight tabular manipulation for exports when needed.
- python-dotenv: Load environment variables (.env) for API keys and DB URI.

Why async? Feed calls and enrichment involve network I/O; async enables efficient concurrency while staying simple and resource-friendly.

### Frontend (React)
- React 18 (react, react-dom): Component-driven UI with hooks.
- React Router (react-router-dom): Client-side routing.
- Tailwind CSS + PostCSS (tailwindcss, postcss, autoprefixer): Utility-first styling for consistent, responsive design.
- Recharts: Accessible charts (Pie, Bar) for severity/type distributions.
- Framer Motion: Subtle animations and transitions to improve information hierarchy and perceived performance.
- Icons (lucide-react): Clean, consistent iconography.
- 3D Globe (three, three-globe, @react-three/fiber, @react-three/drei): Landing page hero visualization of global threat intel connectivity.
- Aux libs: axios (API), clsx + class-variance-authority + tailwind-merge (class composition utilities).

### Tooling & Dev Experience
- react-scripts (CRA): Simple DX for dev server/build/test.
- PowerShell scripts: One-liners to start backend/frontend and run ingestion on Windows.

---

## Data Models and Schemas

### IOC Record (backend/models.py → IOCRecord)
Key fields stored in MongoDB (collection: iocs):
- ioc_value (str): The indicator (IP, domain, URL, hash, CVE, etc.)
- ioc_type (enum): ipv4 | domain | url | md5 | sha1 | sha256 | cve | email
- source (enum): otx | urlhaus | abuseipdb | virustotal | manual
- severity (enum): CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN
- severity_score (int): 0–100 (rule-based)
- vt_detection_rate (float), vt_detections (str like "47/70")
- abuse_score (int): AbuseIPDB confidence
- malware_family (str), threat_actor (str), threat (str)
- correlation_id (uuid), ioc_category (filehash/ip/domain/url/cve/email/other)
- first_seen, last_updated, enrichment_timestamp (UTC datetimes)
- sources (dict): raw provider attributes snapshot

### Stats (router: /api/iocs/stats)
- total_iocs (int)
- by_type (dict of type → count)
- by_severity (dict of severity → count)
- by_source (dict of source → count)
- critical_count, high_count
- recent_count (last 7 days)

---

## Ranking System (Severity Scorer) — Detailed Specification
File: backend/services/severity_scorer.py

Rule-based scoring (accumulate points):

1) VirusTotal detection rate (vt_detection_rate)
- > 0.80 → +50, reason: "VT detection >80%"
- > 0.50 → +30
- > 0.20 → +15

2) Malware family name
- If matches CRITICAL_MALWARE_FAMILIES (e.g., emotet, ryuk, lockbit, cobalt strike, APTs) → +40
- If matches HIGH_RISK_MALWARE_FAMILIES (e.g., ursnif, lokibot, njrat, asyncrat, raccoon, redline) → +25
- Any other non-empty known family → +10

3) AbuseIPDB confidence (ipv4 only)
- > 90 → +30
- > 70 → +20
- > 50 → +10

4) Threat context keywords (context/threat_type/description)
- If contains one of CRITICAL_THREAT_TYPES (e.g., ransomware, c2, apt, 0day) → +25

5) Recency by first_seen
- < 7 days → +15
- < 30 days → +10

6) URLhaus specifics
- url_status == online → +20
- threat indicates malware download → +15

7) VirusTotal reputation
- reputation < -50 → +20

8) Multiple sources corroboration
- ≥ 3 sources → +15
- ≥ 2 sources → +10

Severity buckets:
- score ≥ 70 → CRITICAL
- score ≥ 45 → HIGH
- score ≥ 20 → MEDIUM
- score > 0 → LOW
- else → UNKNOWN

Outputs added to IOC:
- severity (enum), severity_score (int), severity_reasons (list[str])

Notes:
- Scoring is additive and explainable; reasons capture the contributing factors.
- Fields like vt_detections and vt_detection_rate are normalized in direct_ingest before persistence.

---

## Reporting & SIEM Export
File: backend/services/report_generator.py

- Executive Summary metrics (totals, severity distribution, recent 24h, top malware families, type distribution, overall threat level).
- CSV report: sorted by severity_score desc; fields include ioc_value/type/severity/score/malware_family/vt_detections/abuse_score/source/first_seen.
- JSON report: includes executive summary, top threats, actionable blocklist.
- HTML report: styled, printable summary + top 20 threats.
- CEF export: CEF:0|SecInt|ThreatIntel|2.0|... with severity mapping and fields.
- Syslog export: RFC 5424-formatted log lines with key IOC attributes.

---

## API Endpoints (Summary)
Base URL: http://localhost:8000

IOCs
- GET /api/iocs — list IOCs (filters: ioc_type, severity, min_severity, source, limit, offset)
- GET /api/iocs/critical — top CRITICAL IOCs
- GET /api/iocs/recent?hours=24 — recent IOCs
- GET /api/iocs/search?q=term — search by value/description/malware_family/context
- GET /api/iocs/stats — totals and distributions
- GET /api/iocs/export?format=json|csv — export filtered IOCs
- GET /api/iocs/{ioc_value} — detail

Reports
- GET /api/reports/summary — executive summary
- GET /api/reports/top-threats?limit=20 — ranked by severity_score
- GET /api/reports/blocklist — actionable blocklist (+metadata)
- GET /api/reports/download/csv — CSV report (optional severity filter)
- GET /api/reports/download/json — JSON report (include_summary)
- GET /api/reports/download/html — HTML report
- GET /api/reports/export/cef — CEF lines for SIEM
- GET /api/reports/export/syslog — Syslog lines for SIEM

Health
- GET /health/apis — external API health with overall_status (healthy/degraded/unhealthy)

---

## Scripts and How They Work
Root PowerShell scripts (Windows-friendly):

- start-backend.ps1
  - Creates/activates Python venv if missing; installs requirements; starts FastAPI server (reload) at http://localhost:8000
- start-frontend.ps1
  - Installs npm dependencies if missing; launches React dev server at http://localhost:3000
- run-ingestion.ps1
  - Activates venv, runs services/direct_ingest.py, which: fetches OTX pulses + URLhaus URLs/payloads, enriches, scores, stores in MongoDB; prints ingestion summary.
- setup.ps1
  - Checks prerequisites (Python, Node, MongoDB), sets up backend venv and dependencies, installs frontend deps, and prints next steps.

Backend service modules (brief):
- services/threat_feeds.py — Async clients for OTX, URLhaus, VirusTotal, AbuseIPDB; concurrent fetching.
- services/enricher.py — Orchestrates enrichment per IOC type; normalizes VT stats.
- services/severity_scorer.py — Rule-based explainable scoring; bucketization into severity levels.
- services/direct_ingest.py — Development-focused ingestion pipeline (no Kafka); end-to-end store.
- services/report_generator.py — Executive summary + exports (CSV/JSON/HTML/CEF/Syslog).
- services/api_validator.py — API key validation and health/quota report with cache (5 minutes).

Routers:
- routers/iocs.py — Listing, search, stats, export, and detail endpoints.
- routers/reports.py — Summaries, top threats, blocklist, downloads, SIEM formats.

---

## Configuration & Environment
Create backend/.env or root .env (both supported by python-dotenv):

```
MONGO_URI=mongodb://localhost:27017/secint
OTX_API_KEY=...
VIRUSTOTAL_API_KEY=...
ABUSEIPDB_API_KEY=...
URLHAUS_API_KEY=...
```

- MongoDB can be local service or Docker container.
- API keys are optional; features degrade gracefully (some enrichment/feeds disabled if not configured).

---

## Operational Considerations
- Rate Limits: VirusTotal and AbuseIPDB free tiers are rate-limited; enricher enforces small delays and hard caps per batch.
- API Health Caching: /health/apis caches results for 5 minutes to avoid quota burn; pass use_cache=false to force fresh checks.
- Idempotency: direct_ingest checks for existing IOCs by value before insert (basic dedup).
- Timezones: All timestamps stored/returned in UTC ISO8601.

---

## Security & Ethics
- No crawling of illicit infrastructure; feeds are public TI providers.
- Data is for educational/demonstration use and SOC-style workflows.
- Avoids storing credentials/PII; store API keys in environment variables.
- Respect provider ToS and rate limits.

---

## Appendix — Quick Start (Windows)

```powershell
# From repo root
./setup.ps1

# Terminal A: backend
./start-backend.ps1

# Terminal B: frontend
./start-frontend.ps1

# Optional: ingest data
./run-ingestion.ps1
```

Open:
- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health/apis
