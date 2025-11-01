# SecInt v2 - Localhost Quick Start Guide

This guide will help you run the SecInt threat intelligence platform on your local machine without Docker or Kafka.

## Prerequisites

1. **Python 3.9+** installed
2. **Node.js 16+** and npm installed
3. **MongoDB** running locally on port 27017 (or MongoDB Atlas free tier)

## Installation Steps

### 1. Install MongoDB Locally (if not using Atlas)

**Windows:**
- Download MongoDB Community Edition from https://www.mongodb.com/try/download/community
- Install and run MongoDB service
- Default connection: `mongodb://localhost:27017`

**Alternative - MongoDB Atlas (Free Cloud Database):**
- Go to https://www.mongodb.com/atlas
- Create a free account and cluster
- Get your connection string
- Update `.env` file with your connection string

### 2. Setup Backend

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Update .env file with your API keys (optional but recommended)
# Copy .env.example to .env and add your keys:
# - OTX_API_KEY (get from https://otx.alienvault.com/)
# - VIRUSTOTAL_API_KEY (get from https://www.virustotal.com/)
```

### 3. Setup Frontend

```powershell
# Open a new terminal
cd frontend

# Install dependencies
npm install
```

## Running the Application

### Start Backend Server (Terminal 1)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

Backend will run on: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Start Frontend (Terminal 2)

```powershell
cd frontend
npm start
```

Frontend will run on: **http://localhost:3000**

### Ingest Threat Data (Terminal 3 - Optional)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python services/direct_ingest.py
```

This will:
- Fetch threat intelligence from OTX and URLhaus
- Enrich IOCs with VirusTotal data (if API key provided)
- Calculate severity scores
- Store everything in MongoDB

## Testing the Application

1. **Check API Health:**
   - Visit http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

2. **Check Database Connection:**
   - Visit http://localhost:8000/health/apis
   - Shows status of external threat intelligence APIs

3. **View IOC Statistics:**
   - Visit http://localhost:8000/api/iocs/stats
   - Shows counts of IOCs by type, severity, source

4. **Access Frontend Dashboard:**
   - Open http://localhost:3000
   - View IOCs, statistics, and threat intelligence

## Quick Commands

### Backend Commands
```powershell
# Start backend
cd backend; .\venv\Scripts\Activate.ps1; python main.py

# Run ingestion
cd backend; .\venv\Scripts\Activate.ps1; python services/direct_ingest.py

# Run tests
cd backend; .\venv\Scripts\Activate.ps1; pytest tests/
```

### Frontend Commands
```powershell
# Start frontend
cd frontend; npm start

# Build for production
cd frontend; npm run build
```

## Environment Variables

Create `backend/.env` file:

```env
# MongoDB Connection
MONGO_URI=mongodb://localhost:27017/secint

# Threat Intelligence API Keys (Optional)
OTX_API_KEY=your_otx_api_key_here
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here

# AbuseIPDB API Key (Optional)
ABUSEIPDB_API_KEY=your_abuseipdb_key_here
```

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `mongod --version`
- Check connection string in `.env`
- For Atlas: Whitelist your IP address in Atlas dashboard

### Backend Won't Start
- Check Python version: `python --version` (should be 3.9+)
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Won't Start
- Check Node version: `node --version` (should be 16+)
- Clear node_modules and reinstall: `rm -rf node_modules; npm install`

### No Data Showing
- Run the ingestion script: `python services/direct_ingest.py`
- Check MongoDB has data: Use MongoDB Compass or `mongosh`
- Check browser console for errors

## Next Steps

1. **Get API Keys** (Optional but recommended):
   - OTX: https://otx.alienvault.com/
   - VirusTotal: https://www.virustotal.com/
   - AbuseIPDB: https://www.abuseipdb.com/

2. **Schedule Regular Ingestion**:
   - Use Windows Task Scheduler to run `direct_ingest.py` hourly/daily
   - Or run manually when you need fresh threat data

3. **Explore the API**:
   - Visit http://localhost:8000/docs for interactive API documentation
   - Test different endpoints and filters

4. **Export Reports**:
   - Download CSV reports: http://localhost:8000/api/iocs/export?format=csv
   - Generate blocklists: http://localhost:8000/api/reports/blocklist

## Support

For issues or questions:
- Check the logs in the `logs/` directory
- Review API documentation at http://localhost:8000/docs
- Check MongoDB connection and data

Happy Threat Hunting! 🔍🛡️
