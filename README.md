# 🛡️ SecInt - Dark Web Threat Intelligence System

> **A production-ready threat intelligence platform simulating dark web intelligence gathering using verified open-source cybersecurity datasets.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed.svg)](https://www.docker.com/)

**College Capstone Project** | **Security Intelligence** | **Third Year**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Datasets](#datasets)
- [Demo](#demo)
- [Contributing](#contributing)
- [License](#license)
- [Team](#team)

---

## 🎯 Overview

SecInt is an **end-to-end threat intelligence simulation system** designed to demonstrate real-world cybersecurity data pipeline architecture. It processes **350,000+ real threat records** from verified open-source datasets, classifies them using NLP, and visualizes insights through an interactive dashboard.

**Key Capabilities:**
- ✅ Automated dataset ingestion from multiple sources
- ✅ Real-time threat classification using machine learning
- ✅ Scalable message queue architecture with Apache Kafka
- ✅ Interactive analytics dashboard with real-time updates
- ✅ Production-grade error handling and monitoring
- ✅ Full Docker containerization for one-command deployment

---

## ✨ Features

### Backend (FastAPI + MongoDB)
- **Asynchronous REST API** with automatic OpenAPI documentation
- **MongoDB integration** using Motor (async driver) for high-performance queries
- **Aggregation pipelines** for real-time analytics
- **Full-text search** with MongoDB text indexes
- **Request validation** with Pydantic models

### Frontend (React + Tailwind CSS)
- **Real-time dashboard** with auto-refresh (30s polling)
- **Interactive charts** using Recharts (pie charts, bar charts, trends)
- **Debounced search** for efficient threat lookup
- **Responsive design** with Tailwind CSS
- **Error handling** with retry logic and backoff

### Data Pipeline (Kafka + NLP)
- **Kafka message queue** for asynchronous threat processing
- **NLP classification** using TF-IDF + Multinomial Naive Bayes
- **Dataset ingestion** supporting CSV, JSON, and JSONL formats
- **Error tracking** with failed file logging to MongoDB
- **Scalable architecture** processing 350k+ records

### DevOps (Docker Compose)
- **7-service orchestration** (MongoDB, Kafka, Backend, Frontend, Ingestion, Classifier, Zookeeper)
- **Health checks** ensuring services start in correct order
- **Volume management** for data persistence
- **Network isolation** with Docker bridge network
- **One-command deployment** for development and demos

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SecInt System                            │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Dataset     │────▶│  Ingestion  │────▶│    Kafka     │
│   Files      │     │   Service   │     │  (Message    │
│ (CSV/JSON)   │     │  (Python)   │     │   Queue)     │
└──────────────┘     └─────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
                                         ┌──────────────┐
                                         │  Classifier  │
                                         │   Service    │
                                         │ (NLP/TF-IDF) │
                                         └──────┬───────┘
                                                │
                                                ▼
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   React      │◀────│   FastAPI   │◀────│   MongoDB    │
│  Dashboard   │     │   Backend   │     │  (Database)  │
│ (Frontend)   │     │    (API)    │     │              │
└──────────────┘     └─────────────┘     └──────────────┘
```

**Data Flow:**
1. **Ingestion** → Reads CSV/JSON files from `/data` directory
2. **Kafka** → Queues messages for asynchronous processing
3. **Classifier** → Consumes messages, applies NLP classification
4. **MongoDB** → Stores classified threats
5. **Backend API** → Serves aggregated data via REST endpoints
6. **Frontend** → Visualizes insights in real-time dashboard

---

## 🚀 Quick Start

### Prerequisites

Ensure you have:
- ✅ **Docker Desktop** installed and running ([Download](https://www.docker.com/products/docker-desktop))
- ✅ **Git** installed
- ✅ **4GB+ RAM** available
- ✅ **Internet connection** (for first-time Docker image pulls)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/SecInt.git
cd SecInt

# 2. Copy environment configuration
cp .env.example .env

# 3. Start all services (builds Docker images on first run)
docker-compose up --build -d

# 4. Verify services are running
docker ps
```

### Access the System

- **Frontend Dashboard**: http://localhost:3000
- **Backend API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

**⏱️ Wait 1-2 minutes** for initial data ingestion and classification, then refresh the dashboard.

### Stopping the System

```bash
# Stop all containers (preserves data)
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v
```

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

### Getting Started
- **[SETUP.md](./SETUP.md)** - Complete installation and troubleshooting guide
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Development workflow and code guidelines

### For Demos & Presentations
- **[DEMO_GUIDE.md](./DEMO_GUIDE.md)** - Step-by-step demo walkthrough with talking points
- **[DEMO_CHEATSHEET.md](./DEMO_CHEATSHEET.md)** - Quick reference card for presentations

### Technical Documentation (Viva Preparation)
- **[Backend API](./docs/technical_explanation/02_backend.md)** - FastAPI, MongoDB, endpoints, aggregations
- **[Data Pipeline](./docs/)** - Ingestion, Kafka, classification (see docs index)

**📖 Full documentation index**: [docs/README.md](./docs/README.md)

---

## 📊 Datasets

This project uses **350,000+ real cybersecurity threat records** from verified open-source datasets:

| Dataset | Source | Records | Description |
|---------|--------|---------|-------------|
| **Phishing Emails** | Kaggle | ~201,000 | Email phishing campaigns and spam |
| **ExploitDB** | Waiper/ExploitDB_DataSet | ~140,000 | CVE exploits and vulnerability data |
| **Malware MOTIF** | Booz Allen Hamilton | ~7,900 | Malware family classifications |
| **Open-MalSec** | tegridydev/open-malsec | ~530 | Open-source malware intelligence |

**Dataset Structure:**
```
data/
├── phishing_emails/
│   ├── README.md
│   └── raw/
│       └── *.csv
├── exploitdb/
│   ├── README.md
│   └── raw/
│       └── *.json
├── malware_motif/
│   └── raw/
│       └── *.jsonl
└── open_malsec/
    └── raw/
        └── *.json
```

**Note:** Raw dataset files are **not included** in the repository due to size (~500MB). Download instructions are in each dataset's `README.md`.

---

## 🎥 Demo

### Live Demo (After Setup)

1. **Dashboard** (http://localhost:3000)
   - View threat statistics and distributions
   - Interactive pie and bar charts
   - Real-time updates every 30 seconds

2. **Datasets Page**
   - Per-dataset threat counts
   - Ingestion logs with failed file tracking
   - Latest update timestamps

3. **Threats Browser**
   - Search threats by content (debounced)
   - Filter by type and dataset
   - View detailed threat records

### Demo Commands

```bash
# Check ingestion progress
docker logs secint-ingestion

# Watch classification in real-time
docker logs secint-classifier -f

# Verify data in database
docker exec secint-backend python -c "from pymongo import MongoClient; c=MongoClient('mongodb://mongo:27017'); print('Total threats:', c['secint']['threats'].count_documents({}))"

# API query example
curl http://localhost:8000/api/analytics/summary
```

**Full demo script with talking points**: [DEMO_GUIDE.md](./DEMO_GUIDE.md)

---

---

## 🔧 Local Development

Want to run components individually? See [SETUP.md](./SETUP.md#local-development) for detailed instructions.

### Backend Only

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Only

```bash
cd frontend
npm install
npm start
```

### Services Only

```bash
# Run ingestion (requires Kafka)
python backend/services/ingestion.py

# Run classifier (requires Kafka + MongoDB)
python backend/services/classifier.py
```

---

## 🔄 Re-running Ingestion

The ingestion service runs once when the container starts. To re-ingest datasets:

```bash
# Restart the ingestion container
docker-compose restart ingestion

# Check ingestion logs
docker logs secint-ingestion

# View ingestion history in MongoDB
docker exec secint-backend python -c "from pymongo import MongoClient; c=MongoClient('mongodb://mongo:27017'); [print(log) for log in c['secint']['ingestion_logs'].find().sort('timestamp', -1).limit(5)]"
```

**Common Issues:** See [SETUP.md - Troubleshooting](./SETUP.md#troubleshooting) for solutions to:
- NoBrokersAvailable errors
- Dataset path not found
- JSON/CSV parsing errors
- No data appearing in frontend

---

## 📖 API Endpoints

Full interactive documentation at: **http://localhost:8000/docs**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API health check |
| `GET` | `/api/threats` | List threats with filters |
| `GET` | `/api/threats/{id}` | Get specific threat |
| `GET` | `/api/analytics/summary` | Analytics overview |
| `GET` | `/api/datasets/status` | Dataset ingestion status |
| `GET` | `/api/datasets/logs` | Ingestion logs |

**Example Query:**
```bash
# Get all malware threats
curl "http://localhost:8000/api/threats?threat_type=malware&limit=10"

# Get analytics summary
curl http://localhost:8000/api/analytics/summary
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TailwindCSS, Recharts |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Database** | MongoDB (Motor async driver) |
| **Message Queue** | Apache Kafka + Zookeeper |
| **ML/NLP** | scikit-learn (TF-IDF), Transformers |
| **Container** | Docker, Docker Compose |

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

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

---

## � Team

**SecInt** – Security Intelligence Capstone Project

**Contributors:**
- **Your Name** - Project Lead & Full Stack Development
- *(Add teammates here)*

**Institution:** *(Your College/University)*  
**Year:** 2024

---

**🌟 If you found this project useful, please star the repository!**

---

**📧 Questions or feedback?** Open an issue or reach out to the team.


