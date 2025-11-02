# SecInt v2 - Threat Intelligence Platform

<div align="center">

![SecInt v2](https://img.shields.io/badge/SecInt-v2.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-teal?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18.0-61DAFB?style=for-the-badge&logo=react)
![MongoDB](https://img.shields.io/badge/MongoDB-Latest-green?style=for-the-badge&logo=mongodb)

**Real-time Threat Intelligence Aggregation, Enrichment & Analysis Platform**

[Features](#features) • [Architecture](#architecture) • [Installation](#installation) • [Usage](#usage) • [API Documentation](#api-documentation)

</div>

---

## 🎯 Overview

SecInt v2 is a comprehensive threat intelligence platform that automatically collects, enriches, scores, and analyzes Indicators of Compromise (IOCs) from multiple threat feeds. It provides real-time threat intelligence with automated severity scoring, SIEM integration, and an intuitive dashboard for security operations.

### Key Capabilities

- 🌐 **Multi-Source Intelligence** - Aggregates IOCs from AlienVault OTX, VirusTotal, URLhaus, AbuseIPDB
- 🔍 **Intelligent Enrichment** - Type-specific enrichment with reputation scoring and malware analysis
- ⚡ **Automated Severity Scoring** - Weighted algorithm producing CRITICAL/HIGH/MEDIUM/LOW ratings
- 💾 **MongoDB Storage** - 17,500+ IOCs with deduplication and advanced querying
- 📊 **Interactive Dashboard** - Real-time visualization with filters and charts
- 🔐 **SIEM Integration** - CEF and Syslog export formats for Splunk, QRadar, pfSense
- 📈 **API Health Monitoring** - Real-time status tracking of all threat feed APIs
- 📄 **Report Generation** - CSV, JSON, HTML exports with executive summaries

---

## ✨ Features

### 1. **Real-Time Threat Intelligence Ingestion**
- **Automated Collection:**
  - AlienVault OTX: Pulls from threat pulses (limit: 20 pulses)
  - URLhaus: Malware URLs (50) + Payloads (50)
  - On-demand ingestion via dashboard button
  - Background task processing with progress tracking
  
- **Concurrent API Processing:**
  - Asynchronous API calls for high performance
  - Smart rate limiting and quota management
  - Automatic retry with exponential backoff

- **Intelligent Deduplication:**
  - 17,517 unique IOCs currently ingested
  - Correlation ID tracking for SIEM integration
  - Merge strategy for multi-source indicators

- **Supported IOC Types:**
  - 🌐 Domains (75% of dataset)
  - 📍 IPv4 addresses
  - 🔒 File hashes (MD5/SHA1/SHA256)
  - 🔗 URLs
  - 🛡️ CVEs (Common Vulnerabilities)

### 2. **Advanced IOC Enrichment & Severity Scoring**

**Type-Specific Enrichment Pipeline:**

| IOC Type | Enrichment Sources | Data Points |
|----------|-------------------|-------------|
| **IP Addresses** | AbuseIPDB + VirusTotal | Abuse confidence score, geographic data, ISP info, reputation |
| **File Hashes** | VirusTotal | Malware family, detection rate (X/Y engines), behavior analysis |
| **Domains** | VirusTotal + OTX | Reputation score, threat categorization, registration data |
| **URLs** | URLhaus + VirusTotal | Malware distribution, phishing detection, online status |

**Multi-Factor Severity Scoring Algorithm:**

IOCs are ranked using a **weighted 100-point scoring system**:

| Factor | Max Points | Criteria |
|--------|-----------|----------|
| **VirusTotal Detection** | 50 | >80% detection = +50, >50% = +30, >20% = +15 |
| **Malware Family** | 40 | Critical families (Ryuk, Emotet, APT28) = +40 |
| **AbuseIPDB Confidence** | 30 | >90% = +30, >70% = +20, >50% = +10 |
| **Threat Type Context** | 25 | Ransomware, C2, Botnet, APT, Zero-day |
| **URLhaus Activity** | 20 | Online status = +20, Malware download = +15 |
| **VirusTotal Reputation** | 20 | Negative reputation < -50 = +20 |
| **Recency** | 15 | <7 days = +15, <30 days = +10 |
| **Multi-Source Confirmation** | 15 | 3+ sources = +15, 2+ sources = +10 |

**Severity Classification:**

```
Score 70-100+  → 🔴 CRITICAL  (6 IOCs)   - Immediate action required
Score 45-69    → 🟠 HIGH      (27 IOCs)  - Urgent response needed  
Score 20-44    → 🟡 MEDIUM    (46 IOCs)  - Monitor closely
Score 1-19     → 🟢 LOW       (17,438)   - Informational
Score 0        → ⚪ UNKNOWN              - Insufficient data
```

**Example Calculation:**
```
Domain: malicious-c2.com
├─ VT Detection: 62/70 engines (88%)      → +50 points
├─ Malware Family: "Ryuk ransomware"      → +40 points  
├─ Threat Context: "C2 server"            → +25 points
├─ First Seen: 3 days ago                 → +15 points
└─ Confirmed by: 3 sources                → +15 points
────────────────────────────────────────────────────────
   TOTAL: 145 points → CRITICAL severity
```

### 3. **MongoDB Storage & Querying**

**Database Specifications:**
- **Total IOCs:** 17,517 unique indicators
- **Storage Engine:** MongoDB with Motor (async driver)
- **Connection:** `mongodb://localhost:27017/secint`
- **Indexing:** Optimized for `ioc_value`, `severity_score`, `first_seen`

**Rich Metadata Schema:**
```json
{
  "ioc_value": "malware.example.com",
  "ioc_type": "domain",
  "severity": "CRITICAL",
  "severity_score": 85,
  "severity_reasons": ["VT detection >80%", "Critical malware: ryuk"],
  "correlation_id": "uuid-v4-here",
  "threat_actor": "APT28",
  "malware_family": "trojan.reverseshell",
  "vt_detections": "55/76",
  "vt_detection_rate": 0.724,
  "abuse_score": 95,
  "first_seen": "2025-10-31T12:00:00Z",
  "last_updated": "2025-11-02T08:30:00Z",
  "sources": {
    "otx": {...},
    "virustotal": {...},
    "abuseipdb": {...}
  }
}
```

**Advanced Query Capabilities:**
- Filter by type, severity, date range
- Pagination with offset/limit
- Full-text search on IOC values
- Sorting by score, recency, or alphabetical

### 4. **Interactive Dashboard with Data Insights**

**Modern Single-Page Dashboard Features:**

🎯 **Real-Time Statistics Cards:**
- Total IOCs with animated counters (17,517)
- Critical Threats requiring immediate action (6)
- High-Priority Threats (27)  
- Recent IOCs discovered in last 7 days
- Auto-refresh every 30 seconds

📊 **Advanced Visualizations:**

**Severity Distribution Heatmap:**
- Interactive grid: Severity (rows) × IOC Types (columns)
- Color intensity based on count (gradient: gray → gold → yellow)
- Hover tooltips showing exact counts and percentages
- Square cells with colored borders and glow effects
- Visual legend showing intensity scale

**IOC Types Distribution (Logarithmic Bar Chart):**
- Log scale to handle wide data ranges (1 to 21,000)
- Smart axis formatting (21k instead of 21000)
- Data labels on top of each bar
- White axis labels, yellow accents (#F1C40F)
- Rounded bar corners for modern look

💡 **Dynamic Insights Panel:**
Automatically generated analysis beneath the bar chart:
- **Dominant Threat Type:** "DOMAIN accounts for 75% of total IOCs"
- **Activity Multiplier:** "DOMAIN activity is 2.5× higher than average"
- **Critical Alert:** "0.1% of IOCs are CRITICAL severity" (if >5%)
- **Distribution Pattern:** "5 distinct IOC types detected"

**Color-coded bullet points** with context-aware text that updates in real-time!

🔍 **IOC Explorer Table:**
- Paginated list with 100 IOCs per page
- Filter by: Type (Domain, IP, Hash), Severity (All/Critical/High)
- Each row shows: IOC value, Type badge, Severity badge, Score, Sources, Discovery date
- Severity color coding: Red (Critical), Orange (High), Yellow (Medium), Green (Low)

⚡ **Two-Button Refresh Strategy:**
1. **"Ingest New IOCs"** (Green) - Pulls fresh data from threat feeds
   - Shows progress: "Fetching OTX pulses...", "Fetching URLhaus URLs..."
   - Estimated time: 1-3 minutes
   - Auto-refreshes dashboard when complete
   
2. **"Refresh Data"** (Yellow) - Reloads existing data from MongoDB
   - Minimum 1.2s loading animation for visibility
   - Success notification banner
   - Animated stat counters

🏥 **API Health Status:**
- Real-time monitoring of all threat feed APIs
- Status indicators: ✅ OK, ⚠️ Rate Limited, ❌ Not Configured
- Quota tracking: VirusTotal (500/day), AbuseIPDB (1000/day)
- Color-coded cards with hover effects

🎯 **Top 10 Critical Threats:**
- Ranked by severity score (highest first)
- Shows: IOC value, Type, Severity, Score, Threat actor, Malware family
- Numbered ranking badges
- Hover effects with border color changes
- Truncated long values with ellipsis

📥 **Blocklist Download:**
- One-click export of high-severity IOCs
- Firewall-ready format (IPs, domains, hashes separated)
- JSON format for easy parsing
- Includes metadata: generation timestamp, total count

### 5. **Report Generation & Export**
### 5. **Report Generation & Export**

**Multiple Export Formats:**
- **CSV Export** - Tabular format for spreadsheet analysis and pivot tables
- **JSON Export** - Structured data for automation and custom tooling
- **HTML Reports** - Beautifully formatted reports with:
  - Executive summary with key metrics
  - Severity distribution tables
  - Top threats ranked by score
  - Embedded charts and graphs
  - Printable format

**Specialized Exports:**
- **Blocklists** - Firewall-ready IP/domain/hash lists
  - Separated by type (IPv4, domains, URLs, hashes)
  - CRITICAL + HIGH severity only
  - Metadata included (generation time, counts)
  
- **SIEM Integration Formats:**
  - **CEF (Common Event Format)** - For Splunk, QRadar, ArcSight
  - **Syslog (RFC 5424)** - For pfSense, Fortinet, ELK Stack
  - Includes: Severity, correlation IDs, threat actor, timestamps

### 6. **API Health Monitoring**

Real-time monitoring dashboard showing:
- **Status Indicators:** ✅ OK, ⚠️ Rate Limited, ❌ Not Configured, 🔄 Checking
- **Quota Tracking:** 
  - VirusTotal: 500 requests/day
  - AbuseIPDB: 1,000 requests/day  
  - AlienVault OTX: Unlimited
  - URLhaus: Unlimited (public endpoints)
- **Connection Health:** Response time, last successful call
- **Rate Limit Warnings:** Auto-detect approaching limits

### 7. **Dashboard Features Summary**

**Theme:** Dark mode with golden accents (#F1C40F / #0B0C10)

**Key UI Components:**
- 📊 Animated stat cards with ease-out counters
- 🗺️ Severity × Type heatmap with hover tooltips
- 📈 Logarithmic bar chart with axis labels
- 💡 Auto-generated insights panel
- 📋 Filterable IOC explorer table
- 🔄 Dual refresh buttons (Ingest vs Reload)
- ⚡ Progress bars with status messages
- ✅ Success notifications
- 🏥 API health status grid
- 🎯 Top 10 threats ranked list
- 📥 Blocklist download button

**Performance:**
- Auto-refresh: 30s for stats, 2min for API health
- Smooth animations with Framer Motion
- Responsive design (desktop/tablet optimized)
- Minimal 1.2s loading time for visual feedback

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SecInt v2 Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Threat Feeds │───▶│  Enrichment  │───▶│   Severity   │  │
│  │  (OTX, VT,   │    │   Service    │    │   Scoring    │  │
│  │  URLhaus)    │    │              │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │         │
│         └────────────────────┴────────────────────┘         │
│                             ▼                                │
│                    ┌──────────────┐                         │
│                    │   MongoDB    │                         │
│                    │  (17.5K IOCs)│                         │
│                    └──────────────┘                         │
│                             │                                │
│         ┌───────────────────┴───────────────────┐          │
│         ▼                   ▼                   ▼           │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐       │
│  │ FastAPI  │       │  Reports │       │   SIEM   │       │
│  │   REST   │       │  Export  │       │  Export  │       │
│  │   API    │       │(CSV/JSON)│       │(CEF/Syslog)│      │
│  └──────────┘       └──────────┘       └──────────┘       │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────┐         │
│  │         React Dashboard (Port 3000)          │         │
│  │   - IOC Explorer with Filters                │         │
│  │   - Charts & Visualizations                  │         │
│  │   - Top Threats & Blocklists                 │         │
│  │   - API Health Status                        │         │
│  └──────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## � Prerequisites

- **Python 3.11+**
- **Node.js 16+** & npm
- **MongoDB** (localhost:27017 or remote)
- **API Keys** (free tier available):
  - AlienVault OTX API Key
  - VirusTotal API Key
  - AbuseIPDB API Key
  - URLhaus API Key (optional)

---

## 🚀 Quick Start

### 1. Clone the Repository

```powershell
git clone https://github.com/joshi-parwaaz/SecInt.git
cd SecInt
```

### 2. Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install
```

### 4. Configure API Keys

Create a `.env` file in the project root. The backend loads environment variables at startup (we use `python-dotenv`). Required keys used by the code are shown below — remove or leave empty any providers you don't use:

```env
# MongoDB connection (full URI)
MONGO_URI=mongodb://localhost:27017/secint

# Threat Intelligence API keys (leave blank if not available)
OTX_API_KEY=your_otx_api_key_here
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_api_key_here
URLHAUS_API_KEY=your_urlhaus_api_key_here  # optional; public endpoints are available

# Optional / other runtime settings
KAFKA_BROKER=localhost:9092
API_PORT=8000
REACT_APP_API_URL=http://localhost:8000
```

**Get your API keys:**
- [AlienVault OTX](https://otx.alienvault.com/) - Free, unlimited
- [VirusTotal](https://www.virustotal.com/gui/join-us) - Free 500 requests/day
- [AbuseIPDB](https://www.abuseipdb.com/register) - Free 1,000 requests/day
- [URLhaus](https://urlhaus.abuse.ch/) - Free with registration

### 5. Start MongoDB

```powershell
# Windows (if installed as service)
net start MongoDB

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 6. Start the Platform

Run the backend and frontend directly (no PowerShell wrappers required). Open two terminals.

Backend (development, auto-reload):

```powershell
cd backend
# activate venv first if you created one
# Windows
.\venv\Scripts\Activate.ps1
# then run
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend (development):

```powershell
cd frontend
npm start
```

Run ingestion (optional) — if you prefer to run ingestion without the PowerShell script, call the Python ingestion script directly. Example (adjust path/name if you use a different script):

```powershell
cd backend
python -m backend.scripts.backfill_iocs
# or use the provided PowerShell wrapper if you prefer: .\run-ingestion.ps1
```

### 7. Access the Platform

- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health/apis

---

## 📚 API Documentation

Full interactive documentation at: **http://localhost:8000/docs**

### Core Endpoints

#### Get IOCs
```http
GET /api/iocs?limit=100&ioc_type=domain&severity=CRITICAL
```

**Query Parameters:**
- `ioc_type` - Filter by type (ipv4, domain, hash, url, cve)
- `severity` - Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `limit` - Results per page (max 500)
- `offset` - Pagination offset

**Response:**
```json
{
  "iocs": [
    {
      "ioc_value": "malware.example.com",
      "ioc_type": "domain",
      "severity": "CRITICAL",
      "severity_score": 85,
      "malware_family": "trojan.reverseshell",
      "vt_detections": "55/76",
      "correlation_id": "uuid-here",
      "threat_actor": "threat-actor-name",
      "first_seen": "2025-10-31T12:00:00Z"
    }
  ],
  "total": 17517
}
```

#### Get Statistics
```http
GET /api/iocs/stats
```

**Response:**
```json
{
  "total_iocs": 17517,
  "by_type": {
    "domain": 17265,
    "sha256": 122,
    "url": 116,
    "cve": 9,
    "ipv4": 5
  },
  "by_severity": {
    "CRITICAL": 6,
    "HIGH": 27,
    "MEDIUM": 46,
    "LOW": 17438
  },
  "critical_count": 6,
  "high_count": 27
}
```

#### Download Blocklist
```http
GET /api/reports/blocklist
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ipv4_addresses": [],
    "domains": [],
    "urls": [],
    "file_hashes": {
      "md5": [],
      "sha1": [],
      "sha256": ["hash1", "hash2", ...]
    }
  },
  "metadata": {
    "generated_at": "2025-10-31T12:00:00Z",
    "total_iocs": 33
  }
}
```

#### Export Reports
```http
GET /api/reports/download/csv
GET /api/reports/download/json
GET /api/reports/download/html
```

#### SIEM Export
```http
GET /api/reports/export/cef
GET /api/reports/export/syslog
```

#### API Health
```http
GET /health/apis
```

**Response:**
```json
{
  "otx": {
    "status": "ok",
    "quota": "unlimited"
  },
  "virustotal": {
    "status": "ok",
    "quota": "500/day"
  },
  "abuseipdb": {
    "status": "rate_limited",
    "quota": "1000/day"
  }
}
```

---

## 🗂️ Project Structure

```
SecInt/
├── backend/
│   ├── main.py                 # FastAPI application entry
│   ├── database.py             # MongoDB connection
│   ├── models.py               # Pydantic models
│   ├── requirements.txt        # Python dependencies
│   ├── routers/
│   │   ├── iocs.py            # IOC endpoints
│   │   └── reports.py         # Export/SIEM endpoints
│   └── services/
│       ├── threat_feeds.py     # OTX/URLhaus integration and API helpers
│       ├── enricher.py         # VT/AbuseIPDB enrichment orchestrator
│       ├── severity_scorer.py  # Threat severity algorithm (rule-based)
│       ├── direct_ingest.py    # Local ingestion pipeline (no Kafka)
│       └── report_generator.py # CSV/JSON/HTML + SIEM export
├── frontend/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.js             # Main React app
│       ├── index.js
│       └── components/
│           ├── Dashboard.js    # Unified modern dashboard (Explorer + API health)
│           ├── IOCExplorer.js  # Legacy explorer (reference)
│           ├── APIStatus.js    # Legacy API health (reference)
│           └── ui/             # Shared UI primitives (Card, etc.)
├── .env                        # API keys (create this)
├── README.md
├── start-backend.ps1
├── start-frontend.ps1
└── run-ingestion.ps1
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TailwindCSS, Recharts |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Database** | MongoDB (Motor async driver) |
| **Enrichment APIs** | VirusTotal, AbuseIPDB, URLhaus, AlienVault OTX |
| **Deployment** | PowerShell scripts for Windows |

---

## 📊 Data Model

### IOC Record Schema

```python
{
  # Core Identification
  "ioc_value": str,              # The actual indicator (domain, IP, hash, etc.)
  "ioc_type": str,               # ipv4, domain, sha256, url, cve
  "ioc_category": str,           # filehash, ip, domain, url, other
  
  # Severity & Scoring
  "severity": str,               # CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
  "severity_score": int,         # 0-100+ weighted score from algorithm
  "severity_reasons": [str],     # ["VT detection >80%", "Critical malware: ryuk"]
  
  # Tracking & Correlation
  "correlation_id": str,         # UUID for SIEM correlation
  "first_seen": datetime,        # Discovery timestamp
  "last_updated": datetime,      # Last modification
  
  # Threat Attribution
  "threat_actor": str,           # Attribution from OTX pulses
  "malware_family": str,         # Malware classification (e.g., "trojan.emotet")
  "threat_type": str,            # ransomware, c2, botnet, apt
  "description": str,            # Human-readable threat description
  "context": str,                # Additional context from feeds
  
  # Enrichment Data
  "vt_detections": str,          # "X/Y" format (e.g., "55/76")
  "vt_detection_rate": float,    # 0.0-1.0 normalized rate
  "vt_reputation": int,          # -100 to +100 (negative = malicious)
  "abuse_score": int,            # AbuseIPDB confidence (0-100)
  "url_status": str,             # "online" or "offline" (URLhaus)
  
  # Source Tracking
  "source": str,                 # Primary source: otx, urlhaus, virustotal
  "sources": {                   # Raw enrichment data from all sources
    "otx": {
      "pulse_count": int,
      "pulse_names": [str],
      "pulse_ids": [str]
    },
    "virustotal": {
      "detections": int,
      "total_engines": int,
      "scan_date": datetime,
      "permalink": str
    },
    "abuseipdb": {
      "abuse_confidence_score": int,
      "country_code": str,
      "usage_type": str,
      "isp": str
    },
    "urlhaus": {
      "url_status": str,
      "threat": str,
      "tags": [str]
    }
  }
}
```

### Severity Scoring Breakdown

**How Each Factor Contributes:**

```python
# Example: Critical Ransomware C2 Domain
ioc = {
  "ioc_value": "evil-c2.com",
  "ioc_type": "domain"
}

# Scoring breakdown:
factors = {
  "vt_detection_rate": {
    "value": 0.88,                    # 62/70 engines
    "points": 50,                      # >80% detection
    "reason": "VT detection: 62/70 (>80%)"
  },
  "malware_family": {
    "value": "ryuk ransomware",
    "points": 40,                      # Critical family
    "reason": "Critical malware: ryuk"
  },
  "threat_context": {
    "value": "c2 server, command and control",
    "points": 25,                      # Critical threat type
    "reason": "Critical threat type: c2"
  },
  "recency": {
    "value": "3 days old",
    "points": 15,                      # <7 days
    "reason": "Recent threat (<7 days)"
  },
  "multi_source": {
    "value": 3,                        # OTX + VT + URLhaus
    "points": 15,                      # 3 sources
    "reason": "Confirmed by 3 sources"
  }
}

# Total: 145 points → CRITICAL severity
```

### Database Indexes

**Optimized Query Performance:**
```javascript
// MongoDB indexes
db.iocs.createIndex({ "ioc_value": 1 }, { unique: true })
db.iocs.createIndex({ "severity_score": -1 })
db.iocs.createIndex({ "severity": 1, "severity_score": -1 })
db.iocs.createIndex({ "first_seen": -1 })
db.iocs.createIndex({ "ioc_type": 1, "severity": 1 })
db.iocs.createIndex({ "malware_family": 1 })
```

---

## 🔒 Security & Ethics

- ✅ **No live dark web access** (simulation only)
- ✅ **Uses anonymized public datasets**
- ✅ **Network isolation via Docker**
- ✅ **No credential storage or PII**
- ✅ **Educational use only**

**Disclaimer:** This project demonstrates cybersecurity threat intelligence workflows using publicly available datasets. It does not interact with actual dark web infrastructure or illegal activities.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Development workflow (fork → branch → PR)
- Code style guidelines
- Testing requirements
- How to add features (endpoints, components, datasets)

---

## 📄 License

```mermaid
flowchart LR
  subgraph Feeds[External Threat Feeds]
    OTX[AlienVault OTX]
    URLH[URLhaus]
    VT[VirusTotal]
    ABIP[AbuseIPDB]
  end

  OTX --> ING[Direct Ingestion Service]
  URLH --> ING

  ING --> ENR[IOC Enricher (aiohttp)]
  VT --> ENR
  ABIP --> ENR

  ENR --> SC[Severity Scorer]
  SC --> DB[(MongoDB)]

  DB --> IOCAPI[/FastAPI Router: /api/iocs/*/]
  DB --> RPTAPI[/FastAPI Router: /api/reports/*/]

  RPTAPI --> RG[Report Generator\nCSV | JSON | HTML | CEF | Syslog]
  IOCAPI --> FE[React Dashboard (3000)]
  RPTAPI --> FE

  AV[API Validator\n/health/apis] -.-> IOCAPI
  AV -.-> RPTAPI
```


