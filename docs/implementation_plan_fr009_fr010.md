# Implementation Plan: FR-009 & FR-010

This plan covers the final steps of the backend sprint: ensuring cross-origin compatibility for the frontend and performing a comprehensive verification suite.

---

## 1. FR-009: CORS Setup
**Goal**: Enable the Next.js frontend to communicate with the FastAPI backend across domains.

### Technical Tasks
*   [x] **Origin Configuration**: Update `main.py` to support dynamic origin matching or include a wildcard `*` temporarily for the initial Vercel deployment.
*   [x] **Method Restriction**: Explicitly allow only `GET` and `OPTIONS` to follow the principle of least privilege.
*   [x] **Verification**: Use a browser's developer tools or a tool like `curl -H "Origin: http://example.com" -X OPTIONS ...` to verify CORS headers are returned correctly.

---

## 2. FR-010: Local Testing & Validation
**Goal**: Verify the backend is production-ready within the Docker environment.

### Technical Tasks
*   [x] **Ticker Diversity Test**:
    *   Verify `AAPL` (Stock).
    *   Verify `BTC-USD` (Crypto).
    *   Verify `TSLA` (High Volatility Stock).
*   [x] **Analyze Quality Check**: 
    *   Verify that `reasoning` provided by Gemini actually references the ticker and news articles fetched.
    *   Confirm sentiment logic matches the current market context (requires a valid `GEMINI_API_KEY`).
*   [x] **Error Handling Verification**:
    *   Test `INVLD-TKR` → Should return `404 Not Found` with a clear message.
    *   Test trend `INVALID` → Should return `422 Unprocessable Entity`.
*   [x] **Parallel Execution Check**: 
    *   Confirm that a slow Gemini response doesn't block the `/predict` route from serving other users (Uvicorn workers check).

---

## 3. Success Criteria
1.  Frontend at any domain can fetch data from the backend without `CORS` errors.
2.  All test tickers return valid Prophet graphs and Gemini verdicts.
3.  Invalid tickers fail gracefully with standard JSON error envelopes.
