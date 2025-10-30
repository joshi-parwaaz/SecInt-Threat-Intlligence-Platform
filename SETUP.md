# SecInt Setup Guide

Complete setup instructions for running the Dark Web Threat Intelligence system locally.

---

## Prerequisites

Before starting, ensure you have:

- ✅ **Docker Desktop** installed and running ([Download here](https://www.docker.com/products/docker-desktop))
- ✅ **Git** installed ([Download here](https://git-scm.com/downloads))
- ✅ **4GB+ RAM** available for Docker containers
- ✅ **Internet connection** (for first-time Docker image pulls)

**Optional** (for local development without Docker):
- Python 3.10+
- Node.js 18+
- MongoDB 7.0+

---

## Quick Start (Docker - Recommended)

This is the **fastest way** to get the entire system running.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/SecInt.git
cd SecInt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# The default values work for Docker setup - no changes needed
```

### 3. Start All Services

```bash
# Build and start all containers (first time takes 2-3 minutes)
docker-compose up --build -d
```

**Expected output:**
```
✔ Container secint-mongo         Started
✔ Container secint-zookeeper     Started
✔ Container secint-kafka         Healthy (waits ~20s)
✔ Container secint-backend       Started
✔ Container secint-ingestion     Started
✔ Container secint-classifier    Started
✔ Container secint-frontend      Started
```

### 4. Verify Everything is Running

```bash
# Check container status
docker ps

# All 7 containers should show "Up" status
```

### 5. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

**Wait 1-2 minutes** for ingestion and classification to process initial data, then refresh the dashboard.

---

## Understanding the Services

When you run `docker-compose up`, these 7 services start:

| Service | Port | Description |
|---------|------|-------------|
| **mongo** | 27017 | MongoDB database |
| **zookeeper** | 2181 | Kafka coordinator |
| **kafka** | 9092 | Message queue |
| **backend** | 8000 | FastAPI REST API |
| **ingestion** | - | Dataset ingestion service |
| **classifier** | - | NLP threat classifier |
| **frontend** | 3000 | React dashboard |

---

## Checking Logs

### View All Logs
```bash
docker-compose logs -f
```

### View Specific Service Logs
```bash
# Backend API
docker logs secint-backend -f

# Ingestion service (shows dataset processing)
docker logs secint-ingestion -f

# Classifier (shows threat classification)
docker logs secint-classifier -f

# Frontend
docker logs secint-frontend -f
```

**Press Ctrl+C to stop following logs**

---

## Stopping the System

### Stop All Containers (preserves data)
```bash
docker-compose down
```

### Stop and Remove Data (fresh start)
```bash
docker-compose down -v
```

---

## Troubleshooting

### Problem: Containers won't start

**Check if Docker is running:**
```bash
docker ps
```

If you see an error, start Docker Desktop.

---

### Problem: Port conflicts (3000 or 8000 already in use)

**Solution 1: Stop the conflicting application**

**Solution 2: Change ports in docker-compose.yml**
```yaml
frontend:
  ports:
    - "3001:80"  # Change 3000 to 3001

backend:
  ports:
    - "8001:8000"  # Change 8000 to 8001
```

---

### Problem: Kafka unhealthy / ingestion fails

**This is normal!** Kafka takes ~20 seconds to become healthy. The ingestion service waits for this.

**If it persists:**
```bash
docker-compose restart kafka
docker-compose restart ingestion
```

---

### Problem: No data in frontend

**Possible causes:**

1. **Ingestion hasn't completed yet** - Wait 1-2 minutes
2. **Classifier is still processing** - Check logs:
   ```bash
   docker logs secint-classifier --tail=50
   ```
3. **Backend can't connect to MongoDB**:
   ```bash
   docker logs secint-backend --tail=50
   ```

**Verify data in database:**
```bash
docker exec secint-backend python -c "from pymongo import MongoClient; c=MongoClient('mongodb://mongo:27017'); print('Threats:', c['secint']['threats'].count_documents({}))"
```

Should show a number > 0 after ingestion completes.

---

### Problem: "Build failed" errors

**Clear Docker cache and rebuild:**
```bash
docker-compose down
docker system prune -f
docker-compose up --build
```

---

## Local Development (Without Docker)

If you want to develop/debug without Docker:

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB locally (must be running)
# Then run backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Configure local MongoDB:**
Edit `.env`:
```
MONGO_URI=mongodb://localhost:27017/secint
KAFKA_BROKER=localhost:9092
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend runs on http://localhost:3000 and proxies API requests to backend.

---

## Re-running Ingestion

Ingestion runs once when the container starts. To re-ingest:

```bash
# Restart the ingestion container
docker-compose restart ingestion

# Watch the logs
docker logs secint-ingestion -f
```

---

## Adding Your Own Datasets

1. Create folder structure:
   ```
   data/
   └── your_dataset/
       ├── README.md
       ├── raw/
       │   └── your_data.csv  (or .json, .jsonl)
       └── processed/  (empty, for future use)
   ```

2. Update `backend/services/ingestion.py`:
   ```python
   self.datasets = [
       "open_malsec", 
       "malware_motif", 
       "phishing_emails", 
       "exploitdb",
       "your_dataset"  # Add your dataset name
   ]
   ```

3. Rebuild and restart:
   ```bash
   docker-compose build ingestion
   docker-compose restart ingestion
   ```

---

## Data Verification

Run the data verification script to check dataset structure:

```bash
# Inside the backend container
docker exec secint-backend python scripts/verify_data_structure.py

# Or locally
python scripts/verify_data_structure.py
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://mongo:27017/secint` | MongoDB connection string |
| `KAFKA_BROKER` | `kafka:9092` | Kafka broker address |

**For Docker:** Use service names (`mongo`, `kafka`)  
**For local dev:** Use `localhost`

---

## Performance Tips

### For Low-End Machines

If containers are slow:

1. **Reduce resource limits** in docker-compose.yml:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 512M
   ```

2. **Limit ingestion dataset size** - Test with smaller datasets first

3. **Disable classifier** temporarily during development:
   ```bash
   docker-compose up backend frontend mongo -d
   ```

---

## Updating the Project

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose up --build -d
```

---

## Cleaning Up

### Remove Containers and Images
```bash
docker-compose down --rmi all -v
```

### Free Up Disk Space
```bash
docker system prune -a --volumes
```

**Warning:** This removes ALL Docker images/volumes, not just this project.

---

## Next Steps

After successful setup:

1. ✅ Explore the **Frontend Dashboard** - http://localhost:3000
2. ✅ Try the **Interactive API Docs** - http://localhost:8000/docs
3. ✅ Read the **Technical Documentation** - `docs/technical_explanation/`
4. ✅ Check the **Demo Guide** - `DEMO_GUIDE.md`

---

## Getting Help

- **Setup Issues**: Check [Troubleshooting](#troubleshooting) section above
- **Feature Questions**: See [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Technical Details**: Read `docs/technical_explanation/`
- **Found a Bug**: Open an issue on GitHub

---

## System Requirements Summary

**Minimum:**
- 4GB RAM
- 10GB disk space
- Docker Desktop

**Recommended:**
- 8GB RAM
- 20GB disk space
- SSD for better performance

---

**Ready to go!** 🚀 Your SecInt system should be fully operational.
