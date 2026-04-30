<div align="center">

<img src="https://img.shields.io/badge/SecInt-v2.0-yellow?style=for-the-badge&logo=shield&logoColor=black" />
<img src="https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge" />
<img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" />

<br />

# 🛡️ SecInt — Threat Intelligence Platform

**Automated IOC aggregation, enrichment, and severity scoring for Blue Team operations.**

[**Live Dashboard →**](https://secint.vercel.app/) &nbsp;·&nbsp; [**API Explorer →**](https://secint-threat-intlligence-platform.onrender.com/docs) &nbsp;·&nbsp; [**API Health →**](https://secint-threat-intlligence-platform.onrender.com/health)

</div>

---

## What is SecInt?

SecInt is a full-stack threat intelligence platform that continuously aggregates **Indicators of Compromise (IOCs)** from four public threat feeds, enriches each one with cross-source metadata, and ranks them using a 100-point severity scoring algorithm. Everything surfaces in a real-time React dashboard with heatmaps, charts, filterable tables, and one-click report exports.

No commercial subscriptions required. Runs entirely on free-tier infrastructure.

---

## Live Deployment

| Service | URL | Platform |
|---|---|---|
| 🖥️ Frontend | [secint.vercel.app](https://secint.vercel.app/) | Vercel |
| ⚙️ Backend API | [secint-threat-intlligence-platform.onrender.com](https://secint-threat-intlligence-platform.onrender.com/) | Render |
| 📖 Swagger Docs | [/docs](https://secint-threat-intlligence-platform.onrender.com/docs) | Render |

> **Note:** The backend runs on Render's free tier and sleeps after 15 minutes of inactivity. The first request after a sleep period may take 30–60 seconds while the server wakes up. Subsequent requests are instant.

---

## Features

| | Feature | Detail |
|---|---|---|
| 🌐 | **Multi-Source Intelligence** | AlienVault OTX · URLhaus · VirusTotal · AbuseIPDB |
| ⚡ | **Automated Severity Scoring** | 100-point weighted algorithm across detection rates, malware families, and confidence scores |
| 🗺️ | **Interactive Heatmap** | Severity × IOC type cross-matrix with hover tooltips |
| 📊 | **Live Charts** | Bar chart distribution with log scale, animated counters, 30-second auto-refresh |
| 🔍 | **Filterable IOC Explorer** | Filter by type (IPv4, domain, URL, hash, CVE) and severity in real time |
| 📄 | **Report Exports** | Download as CSV, JSON, or HTML — plus a firewall-ready blocklist |
| 🔐 | **SIEM-Ready** | CEF format (Splunk/QRadar) and Syslog format (pfSense/Fortinet) |
| 🤖 | **Auto-Ingestion** | Background scheduler re-pulls feeds every 6 hours when API keys are present |
| 🌱 | **Demo Mode** | 119 realistic seeded IOCs load automatically — no API keys needed to explore |

---

## Tech Stack
Frontend          Backend           Database          Hosting
─────────────     ─────────────     ─────────────     ─────────────
React 18          FastAPI           MongoDB Atlas     Vercel (UI)
Tailwind CSS      Uvicorn           Motor (async)     Render (API)
Recharts          APScheduler
Framer Motion     Motor / PyMongo
React Router      python-dotenv

---

## IOC Coverage

SecInt tracks **7 indicator types** across **4 threat sources**:

| Type | Demo Count | Description |
|---|---|---|
| `ipv4` | 35 | Malicious IP addresses (C2 servers, scanners, botnets) |
| `domain` | 22 | Malicious domains used for phishing, C2, malware delivery |
| `sha256` | 21 | File hashes of known malware samples |
| `url` | 17 | Active malware distribution and phishing URLs |
| `cve` | 11 | Actively exploited vulnerabilities |
| `email` | 8 | Phishing sender addresses |
| `md5` | 5 | Legacy file hashes |

---

## Severity Scoring

Each IOC is scored 0–100 using a weighted multi-signal algorithm:

| Level | Score | Triggers |
|---|---|---|
| 🔴 **CRITICAL** | ≥ 70 | VirusTotal detection > 80%, or known critical family (Emotet, LockBit, Cobalt Strike, BlackCat…) |
| 🟠 **HIGH** | 45–69 | VT detection > 50%, or AbuseIPDB confidence > 70% |
| 🟡 **MEDIUM** | 20–44 | VT detection > 20%, or AbuseIPDB confidence > 50% |
| 🟢 **LOW** | 1–19 | Low-confidence signals only |

---

## API Reference

Full interactive documentation available at [`/docs`](https://secint-threat-intlligence-platform.onrender.com/docs).
GET  /api/iocs/                    List IOCs — filter by type, severity, source
GET  /api/iocs/stats               Aggregated counts (single MongoDB $facet pipeline)
GET  /api/iocs/critical            CRITICAL IOCs sorted by score
GET  /api/iocs/recent              IOCs from the last N hours
GET  /api/iocs/search?q=emotet     Full-text search across value, description, tags
GET  /api/iocs/{value}             Full detail for a single IOC
GET  /api/reports/top-threats      Top N IOCs by severity score
GET  /api/reports/blocklist        Structured blocklist (IPs, domains, hashes, URLs)
GET  /api/reports/download/csv     Export as CSV
GET  /api/reports/download/json    Export as JSON
GET  /api/reports/download/html    Styled HTML threat report
POST /api/ingestion/trigger        Manually trigger a feed refresh
GET  /api/ingestion/status         Live ingestion progress
GET  /health                       Backend health check
GET  /health/apis                  External API key validation status
GET  /health/scheduler             Background scheduler state

---

## Run Locally

**Requirements:** Python 3.11+, Node.js 18+, MongoDB (local or Atlas)

### 1. Clone

```bash
git clone https://github.com/joshi-parwaaz/SecInt-Threat-Intlligence-Platform.git
cd SecInt-Threat-Intlligence-Platform
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy and configure the environment file:

```bash
cp ../.env.example .env
```

Minimum required values in `.env`:

```env
MONGO_URI=mongodb://localhost:27017/secint
CORS_ORIGINS=http://localhost:3000
```

API keys are entirely optional — the platform auto-seeds 119 realistic IOCs on first startup when no keys are present.

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Expected terminal output:
✅ Connected to MongoDB
✅ MongoDB indexes verified
🌱 Demo dataset loaded: 119 IOCs available immediately
⏰ IOC refresh scheduler started

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Frontend

```bash
# New terminal from project root
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
REACT_APP_API_URL=http://localhost:8000
```

```bash
npm start
# Opens at http://localhost:3000
```

---

## Deploy (Free Tier)

Deploy in this order: **Atlas → Render → Vercel**

### 1. MongoDB Atlas

1. Create a free M0 cluster at [cloud.mongodb.com](https://cloud.mongodb.com)
2. **Network Access** → allow `0.0.0.0/0`
3. **Database Access** → create a user, save the password
4. **Connect → Drivers** → copy the connection string and replace `<dbname>` with `secint`

### 2. Render (Backend)

1. New Web Service → connect your GitHub repo
2. Set **Root Directory** to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:

| Variable | Value |
|---|---|
| `MONGO_URI` | Your Atlas connection string |
| `CORS_ORIGINS` | Your Vercel URL (add after step 3) |
| `OTX_API_KEY` | Optional — leave blank for demo mode |
| `VIRUSTOTAL_API_KEY` | Optional |
| `ABUSEIPDB_API_KEY` | Optional |
| `REFRESH_INTERVAL_HOURS` | `6` |

### 3. Vercel (Frontend)

1. New Project → import repo → Root Directory: `frontend`
2. Add environment variable: `REACT_APP_API_URL` = your Render URL
3. Deploy

### 4. Wire them together

Go back to Render → Environment → set `CORS_ORIGINS` to your real Vercel URL → Save.

---

## Get API Keys

All free, no credit card required:

| Provider | Free Limit | Sign Up |
|---|---|---|
| [AlienVault OTX](https://otx.alienvault.com/) | Unlimited | [otx.alienvault.com](https://otx.alienvault.com/) |
| [URLhaus](https://urlhaus.abuse.ch/) | No key needed | — |
| [VirusTotal](https://www.virustotal.com/gui/join-us) | 500 req/day | [virustotal.com](https://www.virustotal.com/gui/join-us) |
| [AbuseIPDB](https://www.abuseipdb.com/register) | 1,000 checks/day | [abuseipdb.com](https://www.abuseipdb.com/register) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Dashboard shows 0 IOCs | Check browser DevTools → Network tab. If `/api/iocs/` returns a 307 redirect, ensure `CORS_ORIGINS` on Render includes your exact Vercel URL |
| Backend 404 on `/dashboard` refresh | Replace `vercel.json` with the SPA fallback config (all routes → `index.html`) |
| `ModuleNotFoundError` on startup | Confirm venv is active: `source venv/bin/activate`, then `pip install -r requirements.txt` |
| MongoDB connection refused | Either start local `mongod` or switch to an Atlas URI in `.env` |
| Render cold start is slow | Expected — free tier sleeps after 15 min. Add [UptimeRobot](https://uptimerobot.com) to ping `/health` every 5 minutes |
| API keys not being picked up | Restart the Render service after adding environment variables |

---

## Project Structure
SecInt-Threat-Intlligence-Platform/
├── backend/
│   ├── main.py                 # FastAPI app, CORS, lifespan
│   ├── database.py             # Motor connection, indexes
│   ├── models.py               # Pydantic models, enums
│   ├── routers/
│   │   ├── iocs.py             # IOC list, stats, search, export
│   │   ├── reports.py          # Top threats, blocklist, downloads
│   │   └── ingestion.py        # Trigger + status endpoints
│   ├── services/
│   │   ├── threat_feeds.py     # OTX, URLhaus, VT, AbuseIPDB clients
│   │   ├── ioc_extractor.py    # Normalises raw feed data → IOCRecord
│   │   ├── enricher.py         # Cross-source enrichment
│   │   ├── severity_scorer.py  # 100-point scoring algorithm
│   │   ├── report_generator.py # CSV / JSON / HTML report builders
│   │   ├── scheduler.py        # APScheduler background refresh
│   │   ├── demo_seeder.py      # Fixture data for demo / no-key mode
│   │   └── api_validator.py    # External API health checks
│   └── data/
│       └── demo_iocs.json      # 119 realistic seed IOCs
└── frontend/
├── src/
│   ├── App.js              # Router, nav, Render wake-up ping
│   ├── components/
│   │   ├── Dashboard.js    # Main dashboard — charts, table, filters
│   │   ├── LandingPage.js  # Landing with live stats + globe
│   │   └── ...
│   └── lib/
│       └── api.js          # Centralised API_BASE config
└── public/

---

## Security & Ethics

- Uses **public threat intelligence feeds only** — no scraping, no dark web access
- All API keys stored as environment variables, never committed to source
- IOC data is used strictly for defensive security research and education
- Respects rate limits of all upstream providers

---

## Contributing

Pull requests are welcome. For significant changes, please open an issue first to discuss what you'd like to change.

```bash
# Run backend tests
cd backend && pytest

# Lint frontend
cd frontend && npm run lint
```

---

## License

[MIT](./LICENSE) — free to use, modify, and distribute.

---

<div align="center">

Built for the Blue Team 🛡️

[Live Demo](https://secint.vercel.app/) · [API Docs](https://secint-threat-intlligence-platform.onrender.com/docs) · [Report a Bug](https://github.com/joshi-parwaaz/SecInt-Threat-Intlligence-Platform/issues)

</div>