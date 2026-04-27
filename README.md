# SecInt — Threat Intelligence Platform

**Live Demo:** https://secint.vercel.app *(update this after deploying)*

Aggregates IOCs from AlienVault OTX, URLhaus, AbuseIPDB, and VirusTotal. Enriches them, scores severity automatically, and surfaces everything in a real-time React dashboard.

> No API keys required to run locally. The app auto-loads a seeded dataset of ~120 realistic IOCs (IPs, domains, hashes, CVEs) on first start.

---

## Stack

| | |
|---|---|
| Frontend | React 18, Tailwind CSS, Recharts, Framer Motion |
| Backend | FastAPI, APScheduler (6-hour IOC auto-refresh) |
| Database | MongoDB via Motor (async) |
| Hosting | Vercel · Render · MongoDB Atlas — all free tier |

---

## Run Locally

**Requirements:** Python 3.10+, Node.js 18+, MongoDB (local or Atlas)

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` file:

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
MONGO_URI=mongodb://localhost:27017/secint   # or your Atlas URI
CORS_ORIGINS=http://localhost:3000
```

API keys are optional — without them the demo dataset loads automatically.

Start the server:

```bash
uvicorn main:app --reload
# Running at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

You should see in the terminal:
```
✅ Connected to MongoDB
✅ MongoDB indexes verified
🌱 Demo dataset loaded: 119 IOCs available immediately
⏰ IOC refresh scheduler started
```

### 2. Frontend

```bash
# New terminal, from project root
cd frontend
npm install
npm start
# Opens at http://localhost:3000
```

The dashboard loads with data immediately. If no API keys are set, a yellow demo mode banner appears at the top.

### Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Make sure venv is active, run `pip install -r requirements.txt` |
| Dashboard shows no data | Visit `http://localhost:8000/api/iocs/stats` — if that returns data, it's a CORS issue. Check `CORS_ORIGINS=http://localhost:3000` in `.env` |
| MongoDB connection refused | Either start local MongoDB (`mongod`) or use an Atlas URI |
| Port 8000 in use | `uvicorn main:app --reload --port 8001` and set `REACT_APP_API_URL=http://localhost:8001` in `frontend/.env` |

---

## Deploy ($0/month)

Deploy in this order: Atlas → Render → Vercel.

### 1. MongoDB Atlas

1. [cloud.mongodb.com](https://cloud.mongodb.com) → free M0 cluster
2. **Network Access** → add `0.0.0.0/0`
3. **Database Access** → create a user, save the password
4. **Connect → Drivers** → copy the connection string, set database to `secint`:
   ```
   mongodb+srv://user:pass@cluster.mongodb.net/secint?retryWrites=true&w=majority
   ```

### 2. Render (backend)

1. Push repo to GitHub
2. [render.com](https://render.com) → New Web Service → connect repo
3. Settings:

   | | |
   |---|---|
   | Root Directory | `backend` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

4. Environment variables (Render dashboard → Environment tab):

   | Key | Value |
   |---|---|
   | `MONGO_URI` | your Atlas connection string |
   | `OTX_API_KEY` | your key, or leave blank for demo mode |
   | `VIRUSTOTAL_API_KEY` | your key, or leave blank |
   | `ABUSEIPDB_API_KEY` | your key, or leave blank |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` (fill after step 3) |
   | `REFRESH_INTERVAL_HOURS` | `6` |

5. Deploy. Verify: `https://secint-api.onrender.com/health` → `{"status":"healthy"}`

> Render free tier sleeps after 15 min of inactivity. Add a free [UptimeRobot](https://uptimerobot.com) monitor pinging `/health` every 5 minutes to keep it awake.

### 3. Vercel (frontend)

```bash
cd frontend
npx vercel
```

When prompted, set the environment variable:
```
REACT_APP_API_URL = https://secint-api.onrender.com
```

Or via the Vercel dashboard: New Project → import repo → Root Directory: `frontend` → add env var above → Deploy.

### 4. Connect them

Go back to Render → Environment → update `CORS_ORIGINS` to your actual Vercel URL → Save (auto-redeploys).

### 5. Update this README

Replace the live demo link at the top with your real Vercel URL. That one line is the most important thing for anyone landing on this repo.

---

## API Endpoints

Full interactive docs at `/docs` when the backend is running.

| Endpoint | Description |
|---|---|
| `GET /api/iocs/` | List IOCs (filter by type, severity, source) |
| `GET /api/iocs/stats` | Counts by type, severity, source — single aggregation |
| `GET /api/iocs/search?q=emotet` | Full-text search |
| `GET /api/iocs/critical` | CRITICAL IOCs only, sorted by score |
| `GET /api/reports/top-threats` | Top N by severity score |
| `GET /api/reports/download/csv` | Export as CSV |
| `GET /api/reports/download/json` | Export as JSON |
| `GET /api/reports/download/html` | Styled HTML report |
| `POST /api/ingestion/trigger` | Manually trigger a feed refresh |
| `GET /health/scheduler` | Background scheduler status |

---

## Severity Scoring

| Level | Score | Criteria |
|---|---|---|
| 🔴 CRITICAL | ≥ 70 | VT detection > 80% or known critical family (Emotet, LockBit, Cobalt Strike…) |
| 🟠 HIGH | 45–69 | VT > 50% or AbuseIPDB confidence > 70% |
| 🟡 MEDIUM | 20–44 | VT > 20% or AbuseIPDB > 50% |
| 🟢 LOW | 1–19 | Low-confidence signals only |

---

## Threat Sources

| Source | Free tier |
|---|---|
| [AlienVault OTX](https://otx.alienvault.com/api) | Unlimited |
| [URLhaus](https://urlhaus.abuse.ch) | No key needed |
| [AbuseIPDB](https://www.abuseipdb.com/account/api) | 1,000 checks/day |
| [VirusTotal](https://www.virustotal.com/gui/my-apikey) | 500 requests/day |
