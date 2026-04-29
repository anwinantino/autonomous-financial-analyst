# PRODUCT REQUIREMENT DOCUMENT (PRD)

## Project: Autonomous Financial Analyst (Hybrid ML + LLM)
**Sprint:** 2-Day MVP  
**Timeline:** Day 1 (Backend) | Day 2 (Frontend + Deployment)

---

## 1. EXECUTIVE SUMMARY
**Vision:** Hybrid system combining time-series price prediction (Prophet) with LLM-powered news validation (Gemini). User enters ticker → gets prediction graph instantly + AI analysis of alignment with current news sentiment.

> [!WARNING]
> **DISCLAIMER:** Not financial advice. Educational tool only.

**MVP Goals:**
- Input ticker (AAPL/BTC-USD) → graph in < 2 seconds
- AI analysis loads asynchronously (3–6 seconds)
- Verdict: **ALIGNED | CONFLICTING | UNCERTAIN**
- Live deployment (single monorepo with Docker)

---

## 2. BUSINESS PROBLEM & SOLUTION
### Problem
- Investors rely on charts without context.
- Price predictions ignore breaking news.
- No way to validate if forecast still makes sense given current events.

### Solution
- Predict price trend using **Prophet** (historical data).
- Fetch relevant news via **DuckDuckGo**.
- Analyze news sentiment with **Gemini LLM**.
- Compare prediction ↔ sentiment → verdict.
- Present all in a single dashboard.

---

## 3. SCOPE (In/Out)
### In Scope
- Time-series forecasting (Prophet, 30-day horizon)
- News retrieval (DuckDuckGo, 5 articles)
- LLM sentiment analysis (Gemini)
- Alignment verdict logic (rule-based)
- React dashboard with Chart.js
- Parallel API calls (fast graph + async analysis)
- Docker containerization (both backend and frontend)
- Single monorepo (backend + frontend folders)
- Deployment: Render (backend via Docker) + Vercel (frontend)
- CORS configuration

### Out of Scope
- User authentication
- Portfolio management
- Real-time streaming
- Database storage
- Advanced trading tools
- Backtesting engine

---

## 4. SYSTEM ARCHITECTURE
### MONOREPO STRUCTURE
```text
project-root/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── main.py
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── package.json
│   ├── app/
│   └── ...
├── docker-compose.yml (optional)
└── .gitignore, README.md
```

### TECH STACK
- **Frontend:** Next.js 14, React, Tailwind, Chart.js
- **Backend:** FastAPI, Uvicorn, Python 3.10+
- **ML:** Prophet, yfinance
- **LLM:** Google Gemini API
- **News:** DuckDuckGo Python library
- **Containerization:** Docker
- **Deploy:** Render (Backend), Vercel (Frontend)

---

## 5. DETAILED FUNCTIONAL REQUIREMENTS
### Backend (Day 1)
- **FR-001: Project Setup & Environment:** Initialize monorepo, Dockerfiles, and dependency management.
- **FR-002: Data Pipeline:** Fetch historical data via `yfinance`.
- **FR-003: Prophet Forecasting:** Train model and generate 30-day forecast.
- **FR-004: News Retrieval:** Fetch 5 relevant articles via DuckDuckGo.
- **FR-005: Gemini LLM Integration:** Analyze sentiment and reasoning.
- **FR-006: Comparator Logic:** Determine alignment between trend and sentiment.
- **FR-007: API Endpoint `/predict`:** Returns forecast data (< 2s).
- **FR-008: API Endpoint `/analyze`:** Returns news analysis (3–6s).
- **FR-009: CORS Setup:** Enable frontend communication.
- **FR-010: Local Testing:** Verify endpoints via Docker.

### Frontend (Day 2)
- **FR-011: UI Layout:** Clean, centered dashboard with Tailwind.
- **FR-012: Chart.js Integration:** Interactive historical + forecast plot.
- **FR-013: Parallel API Calls:** Simultaneous requests for graph and analysis.
- **FR-014: Loading States:** Per-component skeleton/spinners.
- **FR-015: Error Handling:** User-friendly messages for invalid tickers or timeouts.
- **FR-016: Verdict Display:** Color-coded badges (Green/Red/Yellow).
- **FR-017: Performance & UX:** Smooth transitions and mobile responsiveness.

---

## 6. API ENDPOINTS SUMMARY
| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | GET | Health check |
| `/predict` | GET | Get price forecast for graph |
| `/analyze` | GET | Get news analysis + alignment |

---

## 7. SUCCESS CRITERIA
- Graph loads in < 2 seconds.
- Analysis loads in < 6 seconds.
- Correct verdict logic displayed.
- Fully containerized and deployable.
