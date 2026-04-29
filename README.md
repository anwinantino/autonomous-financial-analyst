# Autonomous Financial Analyst

> **Disclaimer:** Educational tool only. Not financial advice.

A hybrid ML + LLM system that combines time-series price prediction (Prophet) with LLM-powered news validation (Gemini) to determine if a stock/crypto forecast aligns with current market sentiment.

---

## Architecture
- **Backend:** FastAPI + Prophet + yfinance + Gemini (Render via Docker)
- **Frontend:** Next.js 14 + Chart.js + Tailwind (Vercel)

## Local Development (Docker)

### Prerequisites
- Docker Desktop installed and running
- A Google Gemini API key

### Setup

1. **Clone the repo and configure environment:**
   ```bash
   cp .env.example backend/.env.local
   # Edit backend/.env.local and add your GEMINI_API_KEY
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Verify:**
   - Backend health: http://localhost:8000/health
   - Frontend: http://localhost:3000

### Run Individually

**Backend:**
```bash
cd backend
docker build -t financial-analyst-backend .
docker run -p 8000:8000 --env-file .env.local financial-analyst-backend
```

**Frontend:**
```bash
cd frontend
docker build -t financial-analyst-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 financial-analyst-frontend
```

---

## API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | GET | Health check |
| `/predict?ticker=AAPL` | GET | 30-day Prophet forecast |
| `/analyze?ticker=AAPL` | GET | News sentiment + alignment verdict |

---

## Deployment
- **Backend:** Render (Docker) — set `Root Directory: backend`
- **Frontend:** Vercel — set `Root Directory: frontend`, env var `NEXT_PUBLIC_API_URL` to your Render URL
