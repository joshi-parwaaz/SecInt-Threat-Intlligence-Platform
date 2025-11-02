# SecInt v2 - Localhost Setup Guide

Step-by-step instructions to run SecInt on your local machine.

---

## Prerequisites

Ensure the following are installed:

1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
2. **Node.js 16+** - [Download](https://nodejs.org/)
3. **MongoDB** - Running on `localhost:27017` or cloud instance

---

## MongoDB Setup

### Option 1: Local Installation

**Windows:**
```powershell
# Download from https://www.mongodb.com/try/download/community
# Install MongoDB Community Edition
# Start MongoDB service
net start MongoDB
```

**Verify connection:**
```powershell
mongosh --eval "db.version()"
```

### Option 2: MongoDB Atlas (Free Cloud)

1. Create account at https://www.mongodb.com/atlas
2. Create free cluster
3. Whitelist your IP address
4. Get connection string (format: `mongodb+srv://<username>:<password>@<cluster>.mongodb.net/secint`)

---

## Backend Setup

### 1. Create Virtual Environment

```powershell
cd backend
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example file and add your API keys:

```powershell
# From project root directory
copy .env.example .env
```

Then edit `.env` file with your API keys:

```env
# MongoDB Connection (required)
MONGO_URI=mongodb://localhost:27017/secint

# Threat Intelligence API Keys (required for full functionality)
OTX_API_KEY=your_otx_api_key_here
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_key_here
URLHAUS_API_KEY=  # Optional - public API available
```

**Get Free API Keys:**
- **OTX:** https://otx.alienvault.com/ (unlimited requests)
- **VirusTotal:** https://www.virustotal.com/ (500 requests/day)
- **AbuseIPDB:** https://www.abuseipdb.com/ (1000 requests/day)

### 5. Start Backend Server

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

---

## Frontend Setup

### 1. Install Dependencies

Open a **new terminal**:

```powershell
cd frontend
npm install
```

### 2. Start Development Server

```powershell
npm start
```

**Expected output:**
```
Compiled successfully!
Local:            http://localhost:3000
```

---

## Data Ingestion

### Run Initial Data Import

Open a **third terminal**:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python services/direct_ingest.py
```

**This will:**
- Fetch threat data from OTX and URLhaus
- Enrich IOCs with VirusTotal/AbuseIPDB data
- Calculate severity scores
- Store in MongoDB

**Estimated time:** 2-5 minutes depending on API keys configured

---

## Verification Steps

### 1. Check Backend Health

Visit: http://localhost:8000/health

**Expected response:**
```json
{
  "status": "healthy"
}
```

### 2. Check API Status

Visit: http://localhost:8000/health/apis

**Shows status of all external APIs:**
- ✅ OK
- ⚠️ Rate Limited
- ❌ Not Configured

### 3. View Statistics

Visit: http://localhost:8000/api/iocs/stats

**Expected response:**
```json
{
  "total_iocs": 17517,
  "by_type": {
    "domain": 17265,
    "sha256": 122,
    "url": 116
  },
  "critical_count": 6,
  "high_count": 27
}
```

### 4. Access Dashboard

Visit: http://localhost:3000

**You should see:**
- Statistics cards with IOC counts
- Severity heatmap visualization
- IOC explorer table
- Top threats list

---

## Quick Commands Reference

### Backend

```powershell
# Start server (development mode with auto-reload)
cd backend; .\venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload

# Run ingestion
cd backend; .\venv\Scripts\Activate.ps1; python services/direct_ingest.py

# View API docs
# Open browser: http://localhost:8000/docs
```

### Frontend

```powershell
# Start development server
cd frontend; npm start

# Build for production
cd frontend; npm run build

# Serve production build
cd frontend; npm install -g serve; serve -s build
```

---

## Troubleshooting

### MongoDB Connection Errors

**Problem:** `ConnectionError: [Errno 111] Connection refused`

**Solutions:**
- Verify MongoDB is running: `mongod --version`
- Check connection string in `.env`
- For Atlas: Ensure IP is whitelisted

### Backend Won't Start

**Problem:** `ModuleNotFoundError` or import errors

**Solutions:**
- Verify Python version: `python --version` (must be 3.11+)
- Ensure venv is activated (prompt should show `(venv)`)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Frontend Build Errors

**Problem:** `npm ERR!` or dependency conflicts

**Solutions:**
- Verify Node version: `node --version` (must be 16+)
- Clear cache and reinstall:
  ```powershell
  rm -rf node_modules package-lock.json
  npm install
  ```

### No Data in Dashboard

**Problem:** Dashboard shows 0 IOCs

**Solutions:**
- Run ingestion script: `python services/direct_ingest.py`
- Check MongoDB has data:
  ```powershell
  mongosh
  use secint
  db.iocs.countDocuments()
  ```
- Check browser console for API errors (F12)

### API Rate Limiting

**Problem:** "Rate limit exceeded" in logs

**Solutions:**
- Free tier limits apply (VirusTotal: 500/day, AbuseIPDB: 1000/day)
- Wait 24 hours for quota reset
- Consider premium API keys for higher limits

---

## Production Deployment

### Build Frontend

```powershell
cd frontend
npm run build
```

### Serve Static Files

Configure FastAPI to serve React build:

```python
# In backend/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")
```

### Run with Production ASGI Server

```powershell
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

---

## Scheduled Ingestion

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → "SecInt Ingestion"
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `services/direct_ingest.py`
   - Start in: `C:\Path\To\SecInt\backend`

### PowerShell Script (Optional)

Create `run-ingestion.ps1`:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python services/direct_ingest.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "Ingestion completed successfully" -ForegroundColor Green
} else {
    Write-Host "Ingestion failed" -ForegroundColor Red
}
```

---

## Next Steps

1. **Explore API Documentation**  
   Visit http://localhost:8000/docs for interactive API testing

2. **Generate Reports**  
   - CSV: `GET /api/reports/download/csv`
   - JSON: `GET /api/reports/download/json`
   - HTML: `GET /api/reports/download/html`

3. **Export for SIEM**  
   - CEF: `GET /api/reports/export/cef`
   - Syslog: `GET /api/reports/export/syslog`

4. **Schedule Regular Updates**  
   Configure automated ingestion to keep threat data current

---

## Support

**Check Logs:**
- Backend: Console output where uvicorn is running
- Frontend: Browser console (F12 → Console tab)
- MongoDB: `mongosh` shell for database queries

**Common Endpoints:**
- Health: http://localhost:8000/health
- API Status: http://localhost:8000/health/apis
- Statistics: http://localhost:8000/api/iocs/stats
- Documentation: http://localhost:8000/docs

---

Happy Threat Hunting! 🔍🛡️
