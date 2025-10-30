# Documentation Index

Welcome to the SecInt Dark Web Threat Intelligence project documentation.

---

## 📚 Quick Navigation

### Getting Started
- **[Setup Guide](../SETUP.md)** - Install and run the system locally
- **[README](../README.md)** - Project overview and features
- **[Contributing](../CONTRIBUTING.md)** - How to contribute to the project

### For Demos & Presentations
- **[Demo Guide](../DEMO_GUIDE.md)** - Step-by-step presentation walkthrough
- **[Demo Cheat Sheet](../DEMO_CHEATSHEET.md)** - Quick reference for demos

### Technical Documentation (Viva Preparation)
- **[Backend API](./technical_explanation/02_backend.md)** - FastAPI, MongoDB, endpoints
- **[Frontend](./technical_explanation/03_frontend.md)** *(Coming soon)* - React, components, UI
- **[Ingestion Service](./technical_explanation/04_ingestion.md)** *(Coming soon)* - Kafka producer, file parsing
- **[Classifier Service](./technical_explanation/05_classifier.md)** *(Coming soon)* - NLP, TF-IDF, Naive Bayes
- **[Docker Architecture](./technical_explanation/06_docker.md)** *(Coming soon)* - Containers, networking, orchestration
- **[Data Pipeline](./technical_explanation/07_data_flow.md)** *(Coming soon)* - End-to-end data lifecycle

---

## 📖 Documentation by Audience

### For Team Members (Setup & Development)
1. Start with [SETUP.md](../SETUP.md) to get the system running
2. Read [CONTRIBUTING.md](../CONTRIBUTING.md) for development workflow
3. Refer to [technical_explanation/](./technical_explanation/) for implementation details

### For Viva/Evaluation Preparation
1. Review [technical_explanation/02_backend.md](./technical_explanation/02_backend.md)
2. Study common viva questions in each technical doc
3. Practice with [DEMO_GUIDE.md](../DEMO_GUIDE.md)

### For External Users/Evaluators
1. Read [README.md](../README.md) for project overview
2. Follow [SETUP.md](../SETUP.md) to run the system
3. Explore the [live demo](http://localhost:3000) (after setup)

---

## 🗂️ Document Descriptions

### Root Level Documentation

#### README.md
- Project overview and features
- Tech stack summary
- Quick start commands
- Dataset information
- License and author details

#### SETUP.md
- Complete installation guide
- Docker setup (recommended)
- Local development setup (optional)
- Troubleshooting common issues
- Environment configuration

#### CONTRIBUTING.md
- Development workflow
- Code style guidelines
- How to add features
- Pull request process

#### DEMO_GUIDE.md
- Comprehensive demo walkthrough
- What to say at each step
- Expected outputs
- Key talking points for teachers
- Emergency troubleshooting

#### DEMO_CHEATSHEET.md
- Quick reference card
- Essential commands only
- Key numbers to remember
- Troubleshooting shortcuts

---

### Technical Explanation (docs/technical_explanation/)

This folder contains in-depth technical documentation for viva preparation. Each document explains:
- **What it does** - Component's role
- **How it works** - Implementation details
- **Why this approach** - Design decisions
- **Common viva questions** - With answers

#### 02_backend.md ✅ (Complete)
- FastAPI application structure
- MongoDB connection with Motor
- Pydantic models and validation
- API endpoints (threats, analytics, datasets)
- Aggregation pipelines
- Error handling
- Performance optimizations

#### 03_frontend.md (Planned)
- React application structure
- Component architecture
- State management
- Tailwind CSS styling
- Charts with Recharts
- API integration
- Polling and retry logic

#### 04_ingestion.md (Planned)
- Kafka producer setup
- File parsing (CSV, JSON, JSONL)
- Error handling for malformed data
- MongoDB logging
- Data validation

#### 05_classifier.md (Planned)
- NLP pipeline
- TF-IDF vectorization
- Multinomial Naive Bayes
- Model training
- Kafka consumer
- Classification confidence

#### 06_docker.md (Planned)
- Docker Compose orchestration
- Service dependencies
- Health checks
- Volume management
- Network configuration
- Multi-stage builds

#### 07_data_flow.md (Planned)
- Complete system data flow
- Lifecycle: Dataset → Kafka → MongoDB → API → UI
- Async processing patterns
- Message queue benefits

---

## 🎯 Documentation Goals

This documentation aims to:
1. ✅ Help teammates set up and run the system quickly
2. ✅ Provide comprehensive technical explanations for viva preparation
3. ✅ Make the project self-explanatory for external evaluators
4. ✅ Serve as a reference during development
5. ✅ Enable easy onboarding of new contributors

---

## 🔄 Documentation Updates

Documentation is living and should be updated when:
- New features are added
- Architecture changes
- Common issues are discovered
- Viva questions reveal knowledge gaps

To update documentation, see [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## 📞 Need Help?

Can't find what you're looking for?

1. **Check the FAQ** in [SETUP.md](../SETUP.md#troubleshooting)
2. **Search existing issues** on GitHub
3. **Open a new issue** with the `documentation` label
4. **Ask the team** in your group chat

---

## 📝 Document Status Legend

- ✅ **Complete** - Ready for use
- 🚧 **In Progress** - Being written
- 📋 **Planned** - Scheduled to be created

---

**Last Updated:** October 30, 2025  
**Maintained By:** SecInt Project Team
