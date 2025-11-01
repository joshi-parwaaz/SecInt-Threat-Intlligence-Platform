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

### 1. **Real Threat Intelligence Ingestion**
- Automated collection from AlienVault OTX pulses
- URLhaus malware distribution tracking
- Concurrent API calls for high performance
- Intelligent deduplication (17,517 unique IOCs ingested)
- Support for: Domains, IP addresses, File hashes (MD5/SHA1/SHA256), URLs, CVEs

### 2. **IOC Enrichment & Severity Scoring**
- **Type-Specific Enrichment:**
  - IPs: AbuseIPDB confidence scores + VirusTotal reputation
  - Hashes: VirusTotal malware analysis with family classification
  - Domains: Reputation scoring and threat categorization
  - URLs: Malware distribution and phishing detection

- **Weighted Severity Algorithm:**
  - VirusTotal detection rate (50 points if >80%)
  - Malware family criticality (40 points for high-threat families)
  - AbuseIPDB confidence (30 points if >90%)
  - IOC recency (15 points if <7 days old)
  
- **Current Threat Landscape:**
  - 6 CRITICAL threats (score ≥80)
  - 27 HIGH threats (score ≥60)
  - 46 MEDIUM threats (score ≥40)

### 3. **Database Storage**
- MongoDB with async motor driver
- 17,517 IOCs stored with rich metadata:
  - `correlation_id` - UUID for SIEM tracking
  - `ioc_category` - Normalized type classification
  - `threat_actor` - Attribution from pulse metadata
  - `last_updated` - Timestamp tracking
  - `vt_detections` - Normalized "X/Y" format
  - `abuse_score` - AbuseIPDB confidence
- Advanced querying with filters, pagination, search

### 4. **Report Generation**
- **CSV Export** - Tabular format for spreadsheet analysis
- **JSON Export** - Structured data for automation
- **HTML Reports** - Formatted reports with executive summaries
- **Blocklists** - Firewall-ready IP/domain/hash lists

### 5. **SIEM Integration**
- **CEF Format** - Common Event Format for Splunk, QRadar, ArcSight
- **Syslog Format** - RFC 5424 compliant for pfSense, Fortinet
- Includes severity, correlation IDs, threat actor attribution

### 6. **API Health Monitoring**
- Real-time status of all threat feed APIs
- Quota tracking (VirusTotal: 500/day)
- Rate limit monitoring
- Connection status indicators

### 7. **Interactive Dashboard**
- **IOC Explorer** - Browse and filter 17.5K IOCs
- **Charts** - Severity distribution, IOC type breakdown
- **Top Threats** - Critical/High priority IOCs for immediate action
- **Blocklist Download** - One-click export for firewall rules
- **Auto-refresh** - 30-second updates for real-time monitoring

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
git clone https://github.com/joshi-parwaaz/Dark-Web-Threat-Crawler.git
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

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=secint

# Threat Intelligence APIs
OTX_API_KEY=your_otx_api_key_here
VIRUSTOTAL_API_KEY=your_vt_api_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_key_here
URLHAUS_API_KEY=your_urlhaus_key_here
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

```powershell
# Start backend (http://localhost:8000)
.\start-backend.ps1

# Start frontend (http://localhost:3000)
.\start-frontend.ps1

# Run threat intelligence ingestion
.\run-ingestion.ps1
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
  "ioc_value": str,              # The actual indicator
  "ioc_type": str,               # ipv4, domain, sha256, url, cve
  "ioc_category": str,           # filehash, ip, domain, url, other
  "severity": str,               # CRITICAL, HIGH, MEDIUM, LOW
  "severity_score": int,         # 0-100 weighted score
  "correlation_id": str,         # UUID for SIEM correlation
  "threat_actor": str,           # Attribution from OTX
  "malware_family": str,         # Malware classification
  "description": str,            # Threat description
  "context": str,                # Additional context
  "vt_detections": str,          # "X/Y" format
  "vt_detection_rate": float,    # 0.0-1.0
  "abuse_score": int,            # AbuseIPDB confidence
  "source": str,                 # otx, urlhaus, virustotal
  "first_seen": datetime,        # Discovery timestamp
  "last_updated": datetime,      # Last modification
  "sources": {                   # Raw enrichment data
    "otx": {},
    "virustotal": {},
    "abuseipdb": {}
  }
}
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


