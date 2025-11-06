# SecInt v2 - Threat Intelligence Platform

<div align="center">

![SecInt v2](https://img.shields.io/badge/SecInt-v2.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-teal?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18.0-61DAFB?style=for-the-badge&logo=react)
![MongoDB](https://img.shields.io/badge/MongoDB-Latest-green?style=for-the-badge&logo=mongodb)

**Automated threat intelligence aggregation with smart severity scoring**

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](./technical_doumentation.md)

</div>

---

## 🎯 What is SecInt?

SecInt v2 automatically aggregates, enriches, and scores **17,500+ Indicators of Compromise (IOCs)** from multiple threat intelligence feeds, providing security teams with actionable insights through an intuitive dashboard.

**In Action:**
- 🔴 **6 CRITICAL** threats requiring immediate action
- 🟠 **27 HIGH** priority threats for urgent response
- 🟡 **46 MEDIUM** threats to monitor
- 📊 **17,517** total IOCs tracked across 5 types

---

## ✨ Key Features

- 🌐 **Multi-Source Intelligence** - Aggregates from AlienVault OTX, VirusTotal, URLhaus, AbuseIPDB
- ⚡ **Automated Severity Scoring** - 100-point weighted algorithm ranking threats by detection rates, malware families, and confidence scores
- 📊 **Interactive Dashboard** - Heatmaps, charts, real-time insights with 30-second auto-refresh
- 🔐 **SIEM Integration** - Export to CEF (Splunk/QRadar) or Syslog (pfSense/Fortinet) formats
- 📄 **Report Generation** - CSV, JSON, HTML exports + firewall-ready blocklists

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+
- MongoDB (localhost:27017 or cloud)
- API keys ([get free keys](#-get-api-keys))

### Installation

```bash
# Clone repository
git clone https://github.com/Arsh-J/SecInt.git
cd SecInt

# Backend setup
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
# From project root
copy .env.example .env  # Windows
# or
cp .env.example .env    # Linux/Mac
```

Edit `.env` with your keys:

```env
MONGO_URI=mongodb://localhost:27017/secint
OTX_API_KEY=your_key_here
VIRUSTOTAL_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
URLHAUS_API_KEY=  # Optional
```

### Run

**Backend (Terminal 1):**
```bash
cd backend
.\venv\Scripts\activate
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm start
```

**Access:**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs

For detailed setup instructions, see [START_LOCALHOST.md](./START_LOCALHOST.md)

---

## 🔑 Get API Keys

| Service | Limit | Link |
|---------|-------|------|
| AlienVault OTX | Unlimited | [Sign Up](https://otx.alienvault.com/) |
| VirusTotal | 500/day | [Register](https://www.virustotal.com/gui/join-us) |
| AbuseIPDB | 1000/day | [Create Account](https://www.abuseipdb.com/register) |
| URLhaus | Unlimited | [Optional](https://urlhaus.abuse.ch/) |

---

## 📊 Example Output

**Dashboard View:**
- Real-time statistics with animated counters
- Severity × Type heatmap visualization
- Logarithmic distribution charts
- Top 10 critical threats ranked by score
- Filterable IOC explorer table

**API Response Example:**
```json
{
  "ioc_value": "malware.example.com",
  "ioc_type": "domain",
  "severity": "CRITICAL",
  "severity_score": 85,
  "malware_family": "trojan.reverseshell",
  "vt_detections": "55/76",
  "threat_actor": "APT28",
  "first_seen": "2025-10-31T12:00:00Z"
}
```

---

## 📚 Documentation

- **[Technical Documentation](./technical_doumentation.md)** - Architecture, data models, scoring algorithm
- **[Setup Guide](./START_LOCALHOST.md)** - Detailed installation and deployment instructions
- **[API Reference](http://localhost:8000/docs)** - Interactive Swagger documentation

---

## 🛠️ Tech Stack

**Frontend:** React 18, TailwindCSS, Recharts, Framer Motion  
**Backend:** FastAPI, Uvicorn, Motor (async MongoDB)  
**Database:** MongoDB  
**APIs:** AlienVault OTX, VirusTotal, AbuseIPDB, URLhaus

---

## 🔒 Security & Ethics

✅ Uses public threat intelligence feeds only  
✅ No live dark web access  
✅ Educational/research purposes  
✅ Respects API provider terms and rate limits

---

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 🙏 Acknowledgments

- AlienVault OTX for threat pulse data
- URLhaus for malware distribution tracking
- VirusTotal & AbuseIPDB for enrichment APIs

---

<div align="center">

**Built with ❤️ for the cybersecurity community**

[Report Bug](https://github.com/joshi-parwaaz/SecInt/issues) • [Request Feature](https://github.com/joshi-parwaaz/SecInt/issues)

</div>
