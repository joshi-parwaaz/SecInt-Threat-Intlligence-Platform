# SecInt v2 — Technical Documentation

Deep dive into the architecture, data models, scoring algorithm, and internal operations of the SecInt v2 Threat Intelligence Platform.

---

## Table of Contents

1. [Architecture & Data Flow](#architecture--data-flow)
2. [Tech Stack & Rationale](#tech-stack--rationale)
3. [Data Models & Schema](#data-models--schema)
4. [Severity Scoring Algorithm](#severity-scoring-algorithm)
5. [API Structure](#api-structure)
6. [Service Modules](#service-modules)
7. [Database Design](#database-design)
8. [Ingestion Pipeline](#ingestion-pipeline)
9. [Reporting & SIEM Export](#reporting--siem-export)
10. [Operational Considerations](#operational-considerations)

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
  IOCAPI --> FE[React Dashboard]
  RPTAPI --> FE

  AV[API Validator\nservices/api_validator.py\n/health/apis] -.-> IOCAPI
  AV -.-> RPTAPI
```

### Data Flow Stages

1. **Collection** - Async fetching from OTX (pulses) and URLhaus (URLs/payloads)
2. **Enrichment** - Type-specific enrichment via VirusTotal and AbuseIPDB
3. **Scoring** - Rule-based severity calculation with explainable factors
4. **Storage** - Async MongoDB insertion with deduplication
5. **Exposure** - FastAPI REST endpoints with filtering/pagination
6. **Visualization** - React dashboard with real-time updates
7. **Export** - SIEM-ready formats (CEF, Syslog) and reports (CSV, JSON, HTML)

---

## Tech Stack & Rationale

### Backend (Python)

| Library | Version | Purpose |
|---------|---------|---------|
| **FastAPI** | 0.104.1 | High-performance web framework with automatic OpenAPI docs |
| **Uvicorn** | latest | ASGI server with hot reload for development |
| **Aiohttp** | latest | Async HTTP client for non-blocking API calls |
| **Motor** | latest | Async MongoDB driver for scalable I/O |
| **PyMongo** | latest | Sync MongoDB operations (fallback) |
| **Pydantic** | v2 | Type-safe data validation and settings management |
| **Pandas** | latest | Tabular data manipulation for exports |
| **python-dotenv** | latest | Environment variable management |

**Why Async?**  
External API calls (OTX, VirusTotal, AbuseIPDB) involve network I/O. Async enables concurrent processing of multiple IOCs without thread overhead, significantly improving ingestion performance.

### Frontend (React)

| Library | Purpose |
|---------|---------|
| **React 18** | Component-driven UI with hooks |
| **React Router** | Client-side routing |
| **TailwindCSS** | Utility-first styling system |
| **Recharts** | Accessible charts (Pie, Bar, Heatmap) |
| **Framer Motion** | Smooth animations and transitions |
| **Lucide React** | Consistent icon library |
| **Axios** | HTTP client for API communication |
| **Three.js** | 3D globe visualization on landing page |

---

## Data Models & Schema

### IOC Record (MongoDB Document)

```javascript
{
  // Core Identification
  "ioc_value": "malware.example.com",      // The indicator itself
  "ioc_type": "domain",                    // ipv4 | domain | url | sha256 | md5 | sha1 | cve | email
  "ioc_category": "domain",                // filehash | ip | domain | url | cve | email | other
  
  // Severity & Scoring
  "severity": "CRITICAL",                  // CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN
  "severity_score": 85,                    // 0-100+ (additive scoring)
  "severity_reasons": [                    // Explainable scoring factors
    "VT detection: 62/70 (>80%)",
    "Critical malware: ryuk"
  ],
  
  // Tracking & Correlation
  "correlation_id": "uuid-v4-here",        // Unique ID for SIEM correlation
  "first_seen": "2025-10-31T12:00:00Z",    // Discovery timestamp (UTC)
  "last_updated": "2025-11-02T08:30:00Z",  // Last modification (UTC)
  "enrichment_timestamp": "2025-11-02T...",// Last enrichment run
  
  // Threat Attribution
  "threat_actor": "APT28",                 // Attribution from OTX
  "malware_family": "trojan.reverseshell", // Normalized malware classification
  "threat_type": "c2",                     // ransomware | c2 | botnet | apt
  "description": "Command and control...", // Human-readable description
  "context": "C2 infrastructure...",       // Additional threat context
  
  // Enrichment Data
  "vt_detections": "55/76",                // VirusTotal detection string
  "vt_detection_rate": 0.724,              // Normalized rate (0.0-1.0)
  "vt_reputation": -65,                    // -100 to +100 (negative = malicious)
  "abuse_score": 95,                       // AbuseIPDB confidence (0-100)
  "url_status": "online",                  // URLhaus: online | offline
  
  // Source Tracking
  "source": "otx",                         // Primary source: otx | urlhaus | virustotal
  "sources": {                             // Raw enrichment data
    "otx": {
      "pulse_count": 3,
      "pulse_names": ["Ryuk Ransomware Campaign"],
      "pulse_ids": ["pulse-uuid"]
    },
    "virustotal": {
      "detections": 55,
      "total_engines": 76,
      "scan_date": "2025-10-31T...",
      "permalink": "https://..."
    },
    "abuseipdb": {
      "abuse_confidence_score": 95,
      "country_code": "RU",
      "usage_type": "Data Center/Web Hosting/Transit",
      "isp": "Example ISP"
    },
    "urlhaus": {
      "url_status": "online",
      "threat": "malware_download",
      "tags": ["emotet", "banking_trojan"]
    }
  }
}
```

### Statistics Response

```javascript
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
  "by_source": {
    "otx": 15234,
    "urlhaus": 2283
  },
  "critical_count": 6,
  "high_count": 27,
  "recent_count": 142  // Last 7 days
}
```

---

## Severity Scoring Algorithm

**File:** `backend/services/severity_scorer.py`

### Rule-Based Scoring System

IOCs accumulate points across multiple factors. Final score determines severity classification.

#### Scoring Factors

| Factor | Max Points | Criteria |
|--------|-----------|----------|
| **VirusTotal Detection Rate** | 50 | >80% = +50, >50% = +30, >20% = +15 |
| **Malware Family** | 40 | Critical families = +40, High-risk = +25, Other = +10 |
| **AbuseIPDB Confidence** | 30 | >90 = +30, >70 = +20, >50 = +10 |
| **Threat Type Context** | 25 | Ransomware, C2, APT, Zero-day = +25 |
| **URLhaus Activity** | 20 | Online = +20, Malware download = +15 |
| **VirusTotal Reputation** | 20 | Reputation < -50 = +20 |
| **Recency** | 15 | <7 days = +15, <30 days = +10 |
| **Multi-Source Confirmation** | 15 | 3+ sources = +15, 2+ sources = +10 |

#### Critical Malware Families

```python
CRITICAL_MALWARE_FAMILIES = {
    'emotet', 'ryuk', 'lockbit', 'blackcat', 'conti',
    'cobalt strike', 'apt28', 'apt29', 'lazarus',
    'wannacry', 'notpetya', 'darkside', 'revil'
}
```

#### High-Risk Malware Families

```python
HIGH_RISK_MALWARE_FAMILIES = {
    'ursnif', 'lokibot', 'njrat', 'asyncrat',
    'raccoon', 'redline', 'azorult', 'formbook'
}
```

#### Critical Threat Types

```python
CRITICAL_THREAT_TYPES = {
    'ransomware', 'c2', 'command and control',
    'apt', 'zero-day', '0day', 'botnet'
}
```

### Severity Classification

```python
if score >= 70:
    severity = "CRITICAL"
elif score >= 45:
    severity = "HIGH"
elif score >= 20:
    severity = "MEDIUM"
elif score > 0:
    severity = "LOW"
else:
    severity = "UNKNOWN"
```

### Example Calculation

**Domain:** `evil-c2.example.com`

```python
factors = {
    "vt_detection_rate": {
        "value": 0.88,              # 62/70 engines
        "points": 50,                # >80% detection
        "reason": "VT detection: 62/70 (>80%)"
    },
    "malware_family": {
        "value": "ryuk ransomware",
        "points": 40,                # Critical family
        "reason": "Critical malware: ryuk"
    },
    "threat_context": {
        "value": "c2 server",
        "points": 25,                # Critical threat type
        "reason": "Critical threat type: c2"
    },
    "recency": {
        "value": "3 days old",
        "points": 15,                # <7 days
        "reason": "Recent threat (<7 days)"
    },
    "multi_source": {
        "value": 3,                  # OTX + VT + URLhaus
        "points": 15,                # 3 sources
        "reason": "Confirmed by 3 sources"
    }
}

# Total: 145 points → CRITICAL severity
```

---

## API Structure

### Base URL
`http://localhost:8000`

### IOC Endpoints (`/api/iocs`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/iocs` | List IOCs with filters |
| GET | `/api/iocs/critical` | Get CRITICAL severity IOCs |
| GET | `/api/iocs/recent` | Get IOCs from last N hours |
| GET | `/api/iocs/search` | Full-text search |
| GET | `/api/iocs/stats` | Get statistics |
| GET | `/api/iocs/export` | Export filtered IOCs |
| GET | `/api/iocs/{ioc_value}` | Get specific IOC details |

**Query Parameters:**
- `ioc_type` - Filter by type (ipv4, domain, hash, url, cve)
- `severity` - Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `min_severity` - Minimum severity level
- `source` - Filter by source (otx, urlhaus)
- `limit` - Results per page (max 500)
- `offset` - Pagination offset

### Report Endpoints (`/api/reports`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/summary` | Executive summary |
| GET | `/api/reports/top-threats` | Top N threats by score |
| GET | `/api/reports/blocklist` | Actionable blocklist |
| GET | `/api/reports/download/csv` | CSV export |
| GET | `/api/reports/download/json` | JSON export |
| GET | `/api/reports/download/html` | HTML report |
| GET | `/api/reports/export/cef` | CEF format (SIEM) |
| GET | `/api/reports/export/syslog` | Syslog format (SIEM) |

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/apis` | External API status |

---

## Service Modules

### `services/threat_feeds.py`

Async clients for external threat intelligence feeds.

**Functions:**
- `fetch_otx_pulses(api_key, limit=20)` - Fetch AlienVault OTX threat pulses
- `fetch_urlhaus_urls(limit=50)` - Fetch recent malicious URLs
- `fetch_urlhaus_payloads(limit=50)` - Fetch malware payload hashes

**Returns:** List of raw IOC dictionaries with metadata

### `services/enricher.py`

Type-specific enrichment orchestrator.

**Functions:**
- `enrich_ioc(ioc, vt_key, abuse_key)` - Main enrichment dispatcher
- `enrich_ip(ip, abuse_key, vt_key)` - AbuseIPDB + VirusTotal
- `enrich_domain(domain, vt_key)` - VirusTotal domain reputation
- `enrich_hash(hash, vt_key)` - VirusTotal file analysis
- `enrich_url(url, vt_key)` - VirusTotal URL scan

**Rate Limiting:**
- VirusTotal: 4 requests/minute (free tier safety margin)
- AbuseIPDB: Respects daily quota (1000 requests/day)

### `services/severity_scorer.py`

Rule-based severity calculation.

**Functions:**
- `calculate_severity(ioc)` - Main scoring function
- Returns: `(severity: str, score: int, reasons: List[str])`

**Logic:**
1. Extract relevant fields (vt_detection_rate, malware_family, etc.)
2. Apply scoring rules additively
3. Classify into severity buckets
4. Generate explainable reasons list

### `services/direct_ingest.py`

Direct ingestion pipeline (no Kafka).

**Workflow:**
1. Fetch IOCs from OTX and URLhaus concurrently
2. For each IOC:
   - Check if already exists in MongoDB
   - Enrich with VirusTotal/AbuseIPDB
   - Calculate severity score
   - Insert/update in database
3. Print summary statistics

**Run:** `python services/direct_ingest.py`

### `services/report_generator.py`

Report and SIEM export generation.

**Functions:**
- `generate_executive_summary(db)` - Aggregated statistics
- `generate_csv_report(db, severity_filter)` - Tabular export
- `generate_json_report(db, include_summary)` - Structured export
- `generate_html_report(db)` - Printable formatted report
- `export_to_cef(db)` - Common Event Format for SIEM
- `export_to_syslog(db)` - RFC 5424 Syslog format

**CEF Format:**
```
CEF:0|SecInt|ThreatIntel|2.0|IOC_DETECTED|Threat Indicator|8|
src=1.2.3.4 dst=0.0.0.0 sev=CRITICAL msg=C2 server detected
cs1=uuid cs1Label=CorrelationID cn1=85 cn1Label=SeverityScore
```

### `services/api_validator.py`

External API health monitoring.

**Functions:**
- `validate_apis(use_cache=True)` - Check all API keys
- Returns: Status dictionary with quota information

**Caching:** Results cached for 5 minutes to avoid quota burn

---

## Database Design

### Collection: `iocs`

**Indexes:**
```javascript
db.iocs.createIndex({ "ioc_value": 1 }, { unique: true })
db.iocs.createIndex({ "severity_score": -1 })
db.iocs.createIndex({ "severity": 1, "severity_score": -1 })
db.iocs.createIndex({ "first_seen": -1 })
db.iocs.createIndex({ "ioc_type": 1, "severity": 1 })
db.iocs.createIndex({ "malware_family": 1 })
```

**Purpose:**
- `ioc_value` - Unique constraint prevents duplicates
- `severity_score` - Fast retrieval of top threats
- `first_seen` - Recent IOC queries
- Compound indexes - Efficient filtered queries

---

## Ingestion Pipeline

### Concurrent Fetching

```python
# Fetch from multiple sources in parallel
otx_task = asyncio.create_task(fetch_otx_pulses(otx_key))
urls_task = asyncio.create_task(fetch_urlhaus_urls())
payloads_task = asyncio.create_task(fetch_urlhaus_payloads())

otx_iocs, urlhaus_urls, urlhaus_payloads = await asyncio.gather(
    otx_task, urls_task, payloads_task
)
```

### Enrichment Flow

```python
for ioc in raw_iocs:
    # Check existence
    existing = await db.iocs.find_one({"ioc_value": ioc["ioc_value"]})
    if existing:
        continue
    
    # Enrich based on type
    enriched = await enrich_ioc(ioc, vt_key, abuse_key)
    
    # Calculate severity
    severity, score, reasons = calculate_severity(enriched)
    enriched.update({
        "severity": severity,
        "severity_score": score,
        "severity_reasons": reasons
    })
    
    # Store
    await db.iocs.insert_one(enriched)
```

---

## Reporting & SIEM Export

### Executive Summary

Includes:
- Total IOC counts
- Severity distribution
- Recent activity (last 24 hours)
- Top malware families
- IOC type breakdown
- Overall threat level assessment

### SIEM Integration

**CEF (Common Event Format):**
- For: Splunk, QRadar, ArcSight
- Severity mapping: CRITICAL=10, HIGH=8, MEDIUM=5, LOW=2
- Fields: src, dst, correlation ID, severity score, malware family

**Syslog (RFC 5424):**
- For: pfSense, Fortinet, ELK Stack
- Priority calculation: `facility * 8 + severity`
- Structured data with IOC attributes

---

## Operational Considerations

### Rate Limiting

**VirusTotal (Free Tier):**
- Limit: 500 requests/day
- Enforced: 4 requests/minute in enricher
- Delay: 15 seconds between requests

**AbuseIPDB (Free Tier):**
- Limit: 1000 requests/day
- Tracked: Daily quota counter
- Fallback: Graceful degradation if quota exceeded

### API Health Caching

`/health/apis` caches results for 5 minutes to prevent quota exhaustion. Pass `?use_cache=false` to force fresh validation.

### Deduplication

Ingestion checks `ioc_value` uniqueness before insertion. Existing IOCs can be updated with fresh enrichment data via update operations.

### Timezone Handling

All timestamps stored and returned in **UTC ISO8601** format for consistency across SIEM integrations.

---

## Design Decisions

### Why MongoDB?

- **Flexible Schema:** IOC enrichment data varies by type and source
- **Scalability:** Handles 17K+ documents with fast indexed queries
- **Async Support:** Motor driver enables non-blocking database operations

### Why Rule-Based Scoring?

- **Explainability:** Each score comes with human-readable reasons
- **Transparency:** Security teams can audit scoring logic
- **Customization:** Easy to add/modify rules without ML training
- **Deterministic:** Same input always produces same output

### Why Direct Ingestion?

- **Simplicity:** No Kafka infrastructure required for development
- **Debugging:** Easier to trace data flow without message queues
- **Prototype:** Sufficient for POC and small-scale deployments
- **Upgrade Path:** Can switch to Kafka-based ingestion for production scale

---

## Security Considerations

- **API Keys:** Stored in environment variables, never committed to version control
- **Rate Limits:** Respected to maintain good standing with providers
- **Data Freshness:** No persistent storage of raw API responses (only processed IOCs)
- **Ethics:** Only uses public threat intelligence feeds, no illegal data sources
- **PII:** No personally identifiable information stored

---

## Known Limitations

1. **Free Tier Quotas:** VirusTotal and AbuseIPDB rate limits restrict enrichment throughput
2. **Batch Processing:** No real-time streaming (ingestion runs on-demand or scheduled)
3. **Deduplication:** Basic value-based; doesn't merge enrichment from multiple runs
4. **Scoring Static:** Manual updates required to add new malware families or threat types
5. **Single Database:** No sharding or replication configured

---

## Future Enhancements

- **Kafka Integration:** For high-throughput real-time ingestion
- **Machine Learning Scoring:** Complement rule-based with ML-based threat prediction
- **Enrichment Caching:** Store VT/AbuseIPDB results to reduce API calls
- **GraphQL API:** Alternative to REST for flexible queries
- **Webhook Alerts:** Real-time notifications for CRITICAL threats
- **Multi-Tenancy:** Support for multiple organizations/teams

---

This documentation provides the technical foundation for understanding, maintaining, and extending SecInt v2.
