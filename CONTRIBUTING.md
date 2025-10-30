# Contributing to SecInt

Thank you for your interest in contributing to the SecInt Dark Web Threat Intelligence project!

## Getting Started

1. **Fork the repository** and clone it locally
2. **Follow the setup guide** in [SETUP.md](./SETUP.md)
3. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### 1. Make Your Changes

- Write clean, documented code
- Follow existing code style and patterns
- Add comments for complex logic
- Update relevant documentation

### 2. Test Locally

Before committing, ensure your changes work:

```bash
# Start the full stack
docker-compose up --build

# Check logs for errors
docker logs secint-backend
docker logs secint-classifier
docker logs secint-ingestion

# Test the API
curl http://localhost:8000/health

# Test the frontend
# Open http://localhost:3000 in browser
```

### 3. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: Brief description of what you added"

# For bug fixes:
git commit -m "Fix: Description of the bug fixed"

# For documentation:
git commit -m "Docs: Update setup instructions"
```

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- **Clear title** describing the change
- **Description** of what changed and why
- **Testing steps** so reviewers can verify

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for functions and classes
- Keep functions focused and single-purpose

### JavaScript/React (Frontend)
- Use functional components with hooks
- Keep components small and reusable
- Use meaningful variable names
- Add comments for complex UI logic

### Docker
- Keep Dockerfiles minimal
- Use multi-stage builds where appropriate
- Document environment variables

## Project Structure

```
SecInt/
├── backend/           # FastAPI application
│   ├── main.py       # App entry point
│   ├── database.py   # MongoDB connection
│   ├── models.py     # Pydantic models
│   ├── routers/      # API endpoints
│   └── services/     # Ingestion & classifier
├── frontend/         # React application
│   └── src/
│       └── components/
├── data/             # Dataset structure (not tracked)
├── docs/             # Documentation
├── scripts/          # Helper scripts
└── docker-compose.yml
```

## Adding New Features

### Backend Endpoint
1. Add Pydantic model in `models.py`
2. Create router function in appropriate `routers/` file
3. Update API documentation in `docs/`
4. Test with Swagger UI at `/docs`

### Frontend Component
1. Create component in `src/components/`
2. Follow existing patterns (Dashboard, Threats, Datasets)
3. Use Tailwind for styling
4. Add to routing in `App.js` if needed

### New Dataset
1. Add dataset folder under `data/your_dataset/`
2. Create `README.md` explaining the dataset
3. Update `services/ingestion.py` to recognize it
4. Update `verify_data_structure.py` if needed

## Need Help?

- **Documentation**: Check `docs/` folder
- **Setup Issues**: See [SETUP.md](./SETUP.md)
- **Viva Prep**: Read technical explanations in `docs/technical_explanation/`
- **Questions**: Open an issue on GitHub

## Team Members

This is a college capstone project. All team members have equal contribution rights.

---

**Thank you for contributing to SecInt!** 🚀
