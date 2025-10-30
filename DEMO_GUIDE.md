# 🎓 SecInt Demo Guide for Teacher Presentation

This guide will walk you through running the entire Dark Web Threat Intelligence system from scratch in front of your teacher.

---

## 📋 Pre-Demo Checklist

Before your presentation, ensure:
- [ ] Docker Desktop is installed and **running**
- [ ] You're in the project directory: `D:\Work\code\SecInt`
- [ ] Your computer has internet access (for initial Docker image pulls)
- [ ] PowerShell or terminal is ready

**Estimated total demo time:** 5-10 minutes (after first-time setup)

---

## 🎬 Demo Script

### Part 1: Introduction (30 seconds)

**What to say:**
> "I've built a production-ready Dark Web Threat Intelligence system that simulates real-world cybersecurity threat analysis. It ingests 350,000+ real threat records from 4 datasets, classifies them using NLP, and visualizes the results in a modern dashboard."

**Show them:**
- The project folder structure in VS Code
- The `docker-compose.yml` file (explain: "7 microservices orchestrated")

---

### Part 2: Starting the System (2-3 minutes)

**Step 1: Clean Start**
```powershell
# Navigate to project
cd D:\Work\code\SecInt

# Stop any previous containers
docker-compose down
```

**What to say:**
> "First, I'll ensure we start with a clean slate. This removes any previous containers."

**Expected output:**
```
✔ Container secint-frontend    Removed
✔ Container secint-classifier  Removed
✔ Container secint-ingestion   Removed
...
```

---

**Step 2: Build and Start All Services**
```powershell
docker-compose up --build -d
```

**What to say:**
> "Now I'll build and start all 7 services:
> - MongoDB for data storage
> - Zookeeper and Kafka for the message queue
> - Backend FastAPI server
> - Ingestion service to load datasets
> - Classifier service with NLP
> - React frontend dashboard"

**Expected output:**
```
[+] Running 12/12
 ✔ Network secint_secint-network  Created
 ✔ Container secint-zookeeper     Started
 ✔ Container secint-mongo         Started
 ✔ Container secint-kafka         Healthy  (waits ~20s for healthcheck)
 ✔ Container secint-ingestion     Started
 ✔ Container secint-classifier    Started
 ✔ Container secint-backend       Started
 ✔ Container secint-frontend      Started
```

**Note:** Kafka healthcheck takes ~20 seconds. Explain this is intentional to ensure services start in correct order.

---

**Step 3: Verify All Services Running**
```powershell
docker ps
```

**What to say:**
> "All 7 containers should show 'Up' status. Notice Kafka shows 'healthy'."

**Expected output:**
```
CONTAINER ID   IMAGE                 STATUS
463cbd5104d0   secint-frontend       Up 28 seconds
2be6f8bcc3d2   secint-backend        Up 28 seconds
bfba0ad241bc   secint-ingestion      Up 11 seconds
ffc102437298   secint-classifier     Up 11 seconds
0dc965f3f283   cp-kafka:7.5.0        Up 29 seconds (healthy)
828175e4d7be   cp-zookeeper:7.5.0    Up 30 seconds
dec107354884   mongo:7.0             Up 29 seconds
```

---

### Part 3: Watch the Pipeline Work (2 minutes)

**Step 4: Check Ingestion Logs**
```powershell
docker logs secint-ingestion --tail=20
```

**What to say:**
> "The ingestion service scans our data folder, reads CSV and JSON files, and publishes them to Kafka. Here we can see it processing 4 datasets."

**Expected output:**
```
INFO:__main__:Starting ingestion for 4 datasets...
ERROR:__main__:Failed to process .../phishing-email-inbound.json: Expecting property name...
INFO:__main__:✅ Ingested open_malsec: 532 records sent, 1 failed
INFO:__main__:✅ Ingested malware_motif: 7919 records sent, 0 failed
INFO:__main__:✅ Ingested phishing_emails: 201048 records sent, 0 failed
INFO:__main__:✅ Ingested exploitdb: 140466 records sent, 0 failed
INFO:__main__:🎉 Ingestion complete: 349965 records processed, 1 failed
```

**Key point to mention:**
> "Notice one file has a JSON error—this is a malformed file in the source dataset. Our system logs it but continues processing. This is production-grade error handling."

---

**Step 5: Watch the Classifier**
```powershell
docker logs secint-classifier --tail=30
```

**What to say:**
> "The classifier consumes messages from Kafka, uses TF-IDF and Naive Bayes to categorize threats, and writes results to MongoDB."

**Expected output:**
```
INFO:__main__:✅ Classified phishing_emails record as credential_leak (confidence: 0.20)
INFO:__main__:✅ Classified malware_motif record as credential_leak (confidence: 0.20)
INFO:__main__:✅ Classified exploitdb record as exploit (confidence: 0.35)
...
```

---

**Step 6: Check Database**
```powershell
docker exec secint-backend python -c "from pymongo import MongoClient; c=MongoClient('mongodb://mongo:27017'); db=c['secint']; print('Total threats classified:', db['threats'].count_documents({}))"
```

**What to say:**
> "Let's verify data is in MongoDB. We should see thousands of classified threats."

**Expected output:**
```
Total threats classified: 8500
```
(Number will keep growing as classifier processes the queue)

---

### Part 4: The Dashboard (3-4 minutes)

**Step 7: Open the Frontend**

Open browser to: **http://localhost:3000**

**What to say:**
> "This is the React dashboard with real-time threat intelligence visualization."

**Walk through each page:**

#### **1. Dashboard Page**
Point out:
- **Total Threats** counter (updates every 30s via polling)
- **Threat Type Distribution** pie chart with custom labels
- **Trends** bar chart showing threat categories
- **Recent Threats** feed at the bottom

**Demonstrate:**
- Wait 30 seconds and refresh — numbers update automatically
- Hover over chart elements to show custom tooltips

---

#### **2. Datasets Page** (click "Datasets" in nav)
Point out:
- 4 dataset cards with stats
- Records processed, unique threat types, last update time
- Failed files section (shows the 1 malformed JSON file)

**What to say:**
> "This aggregates data directly from MongoDB, showing per-dataset statistics and any ingestion errors with file paths and error messages."

---

#### **3. Threats Page** (click "Threats" in nav)
Point out:
- Search bar (debounced, minimum 3 characters)
- Filter dropdowns for threat type and dataset
- Individual threat cards with metadata

**Demonstrate:**
- Type "phish" in search (wait for debounce)
- Select "credential_leak" from threat type filter
- Show pagination

**What to say:**
> "The search uses MongoDB text indexing for full-text search across threat content. The UI implements debouncing to avoid spamming the backend."

---

**Step 8: Show API Documentation**

Open browser to: **http://localhost:8000/docs**

**What to say:**
> "FastAPI auto-generates interactive API documentation. All endpoints are documented with request/response schemas."

**Click on:**
- `GET /api/analytics/summary` → Try it out → Execute
- Show the JSON response

---

### Part 5: Architecture Explanation (1-2 minutes)

**Open `docker-compose.yml` in VS Code**

**What to say:**
> "Let me explain the architecture:
> 
> 1. **Data Ingestion:** Python script reads CSV/JSON files → publishes to Kafka
> 2. **Message Queue:** Kafka decouples ingestion from classification for scalability
> 3. **NLP Classification:** Consumes from Kafka → TF-IDF + Naive Bayes → writes to MongoDB
> 4. **API Layer:** FastAPI serves REST endpoints with async MongoDB queries
> 5. **Frontend:** React app with Recharts visualization
> 6. **Orchestration:** Docker Compose manages all services with health checks and restart policies"

**Show key files:**
- `backend/services/ingestion.py` — data loading logic
- `backend/services/classifier.py` — NLP classification
- `backend/routers/analytics.py` — aggregation endpoints
- `frontend/src/components/Dashboard.js` — React charts

---

### Part 6: Error Handling Demo (Optional, 1 minute)

**What to say:**
> "Let me demonstrate the enhanced error tracking I implemented."

```powershell
docker exec secint-backend python -c "from pymongo import MongoClient; import json; c=MongoClient('mongodb://mongo:27017'); logs=list(c['secint']['ingestion_logs'].find({'dataset': 'open_malsec'}).sort('timestamp', -1).limit(1)); print(json.dumps(logs[0] if logs else {}, indent=2, default=str))"
```

**Expected output:**
```json
{
  "_id": "...",
  "dataset": "open_malsec",
  "records_processed": 532,
  "records_failed": 1,
  "failed_files": [
    {
      "file": "open_malsec/raw/open-malsec/phishing-email-inbound.json",
      "error": "Expecting property name enclosed in double quotes: line 622..."
    }
  ],
  "status": "completed_with_errors",
  "timestamp": "2025-10-30 ..."
}
```

**What to say:**
> "Each ingestion run is logged with failed files, error messages, and timestamps. This makes debugging production issues much easier."

---

## 🎯 Key Talking Points for Teacher

### Technical Sophistication:
1. **Microservices Architecture** — 7 independent services communicating via REST and Kafka
2. **Asynchronous Processing** — FastAPI with async/await, Kafka message queue
3. **Production Practices:**
   - Health checks (Kafka waits before dependent services start)
   - Restart policies (auto-recovery from failures)
   - Error logging to MongoDB
   - Retry logic with exponential backoff in frontend

### Real-World Data:
- **350,000+ real threat records** from verified cybersecurity datasets:
  - Phishing emails (Kaggle)
  - Malware campaigns (Booz Allen MOTIF)
  - Exploit metadata (ExploitDB)
  - Open-source malware intelligence

### NLP/ML Component:
- TF-IDF vectorization for text feature extraction
- Multinomial Naive Bayes for classification
- Confidence scores included with predictions
- Extensible to transformers/BERT (future work)

### Full-Stack Expertise:
- **Backend:** Python, FastAPI, MongoDB (Motor async driver), Kafka
- **Frontend:** React, Tailwind CSS, Recharts
- **DevOps:** Docker multi-stage builds, Docker Compose orchestration

---

## ⚡ Quick Commands Reference

### Restart Everything
```powershell
docker-compose down
docker-compose up --build -d
```

### Re-run Ingestion Only
```powershell
docker-compose restart ingestion
docker logs secint-ingestion -f
```

### Check Logs
```powershell
docker logs secint-backend --tail=50
docker logs secint-classifier --tail=50
docker logs secint-ingestion --tail=50
```

### Check Database Stats
```powershell
# Total threats
docker exec secint-backend python -c "from pymongo import MongoClient; c=MongoClient('mongodb://mongo:27017'); print(c['secint']['threats'].count_documents({}))"

# Ingestion logs
docker exec secint-backend python -c "from pymongo import MongoClient; c=MongoClient('mongodb://mongo:27017'); print(c['secint']['ingestion_logs'].count_documents({}))"
```

### Stop Everything
```powershell
docker-compose down
```

---

## 🐛 Troubleshooting During Demo

### If services don't start:
1. **Check Docker is running:** Look for Docker icon in system tray
2. **Kafka not healthy?** Wait 30 seconds — healthcheck needs time
3. **Port conflicts?** Stop other apps using 3000, 8000, 27017, 9092

### If frontend shows no data:
1. **Check backend:** Visit http://localhost:8000/docs — should load
2. **Check ingestion:** `docker logs secint-ingestion` — should show "Ingestion complete"
3. **Wait:** Classifier may still be processing — check `docker logs secint-classifier`

### If MongoDB shows 0 threats:
- **Ingestion just started:** Check `docker logs secint-ingestion` for progress
- **Classifier lag:** Check `docker logs secint-classifier` — should show "Classified X record"
- **Wait 1-2 minutes** for full pipeline to process initial batch

---

## 📊 Expected Numbers (After Full Ingestion)

| Metric | Value |
|--------|-------|
| Total Threats Processed | ~349,965 |
| Datasets | 4 (open_malsec, malware_motif, phishing_emails, exploitdb) |
| Phishing Emails | ~201,048 |
| ExploitDB Entries | ~140,466 |
| Malware MOTIF | ~7,919 |
| Open-MalSec | ~532 |
| Failed Files | 1 (known malformed JSON) |

---

## 🏆 Closing Remarks

**What to say:**
> "This project demonstrates:
> - End-to-end data pipeline design
> - Microservices architecture with message queues
> - NLP-based classification at scale
> - Production-ready error handling and monitoring
> - Modern full-stack development with React and FastAPI
> - Container orchestration with Docker Compose
> 
> All using real cybersecurity datasets to simulate a threat intelligence platform that companies like CrowdStrike or Recorded Future would use."

---

## 📝 Notes

- **First run** may take 2-3 minutes to pull Docker images
- **Subsequent runs** start in ~30 seconds
- **Ingestion** completes in ~1 minute for all datasets
- **Classification** continues in background (can take 5-10 minutes for all 350k records)
- **Frontend** is responsive and shows data as it arrives

Good luck with your presentation! 🚀
