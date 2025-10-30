# 📄 SecInt Demo Cheat Sheet

## Quick Start Commands

```powershell
# 1. Clean start
docker-compose down

# 2. Build and start everything
docker-compose up --build -d

# 3. Check status
docker ps

# 4. Watch ingestion logs
docker logs secint-ingestion -f

# 5. Watch classifier logs
docker logs secint-classifier -f

# 6. Check threat count
docker exec secint-backend python -c "from pymongo import MongoClient; c=MongoClient('mongodb://mongo:27017'); db=c['secint']; print('Threats:', db['threats'].count_documents({}))"
```

## Access Points

- **Frontend Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **API Base:** http://localhost:8000

## Demo Flow (5 minutes)

1. **Start:** `docker-compose down && docker-compose up --build -d`
2. **Wait:** 20-30 seconds for Kafka healthcheck
3. **Show Logs:** `docker logs secint-ingestion` (ingestion summary)
4. **Check DB:** Run threat count command above
5. **Open Browser:** Visit http://localhost:3000
6. **Walk Through:**
   - Dashboard (pie chart, bar chart, stats)
   - Datasets (4 cards, error tracking)
   - Threats (search, filters, pagination)
7. **Show API:** http://localhost:8000/docs → Try `/api/analytics/summary`

## Key Numbers

- **Total Records:** ~350,000
- **Datasets:** 4
- **Services:** 7
- **Failed Files:** 1 (malformed JSON - expected)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No data in frontend | Wait 1-2 min for ingestion + classification |
| Kafka unhealthy | Wait 30 seconds for healthcheck |
| Port conflict | Stop other apps on 3000/8000/27017/9092 |
| Docker error | Ensure Docker Desktop is running |

## Talking Points

- 350k+ real cybersecurity threat records
- NLP classification (TF-IDF + Naive Bayes)
- Microservices architecture (7 services)
- Kafka message queue for scalability
- Production error handling (logs failed files to MongoDB)
- Real-time dashboard with polling
- Full Docker Compose orchestration

## Architecture

```
Data Files → Ingestion → Kafka → Classifier → MongoDB
                                                   ↓
                                              FastAPI Backend
                                                   ↓
                                            React Frontend
```

## Emergency Commands

```powershell
# Restart ingestion
docker-compose restart ingestion

# View all logs
docker-compose logs -f

# Check specific service
docker logs secint-backend --tail=50

# Stop everything
docker-compose down

# Nuclear option (full cleanup)
docker-compose down -v
docker system prune -f
```
