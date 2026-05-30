# Security Simulation MVP

Backend: FastAPI + SQLAlchemy
Frontend: React + TypeScript + Vite
Database: PostgreSQL-ready, SQLite fallback for local bootstrapping

## Run backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run frontend

```bash
cd apps/web
npm install
npm run dev
```

## Run tests

```bash
cd apps/api
pytest
```
