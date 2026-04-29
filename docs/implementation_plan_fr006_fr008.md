# Implementation Plan: FR-006, FR-007, FR-008

This plan focuses on finalizing the backend endpoints, optimizing performance to meet sub-2-second targets, and ensuring logical alignment between ML forecasts and LLM sentiment.

---

## 1. FR-006: Comparator Logic Refinement
**Goal**: Implement a rule-based engine to compare Prophet trends with Gemini sentiment.

### Technical Tasks
*   [ ] **Refine `comparator.py`**:
    *   Map `UP/DOWN` signals to a unified internal direction.
    *   Map `POSITIVE/NEGATIVE` signals to a unified internal direction.
    *   **Verdict Matrix**:
        *   `ALIGNED`: Both signals match (e.g., UP and POSITIVE).
        *   `CONFLICTING`: Signals are opposite (e.g., UP and NEGATIVE).
        *   `UNCERTAIN`: One or both signals are `NEUTRAL` or missing.
*   [ ] **Confidence Scoring**: Implement a score based on ML model accuracy and LLM sentiment confidence.

---

## 2. FR-007: `/predict` Optimization & Caching
**Goal**: Return 30-day forecasts in < 2 seconds with a 5-minute TTL.

### Technical Tasks
*   [ ] **TTL Adjustment**: Update `CACHE_TTL` in `prophet_ml.py` from 24 hours to **5 minutes** (300 seconds).
*   [ ] **Speed Optimization**:
    *   Reduce historical data fetch period from 2 years to **1 year** to minimize `yfinance` download time.
    *   Ensure cached model loading is optimized for disk I/O.
*   [ ] **Schema Compliance**: Verify response matches the PRD structure.

---

## 3. FR-008: `/analyze` Endpoint Performance
**Goal**: Provide news and AI alignment in 3–6 seconds.

### Technical Tasks
*   [ ] **Parallelization**: Confirm `fetch_news` and `analyze_sentiment` run asynchronously to minimize total wait time.
*   [ ] **Schema Verification**: Ensure response includes `news`, `sentiment`, `verdict`, and `reasoning`.
*   [ ] **Graceful Degradation**: If LLM exceeds 5 seconds, return the news articles with an "UNCERTAIN" verdict to maintain the 6-second overall response target.

---

## 4. Verification & Testing
*   [ ] **Latency Check**: Verify `/predict` is < 2s and `/analyze` is < 6s.
*   [ ] **Cache Test**: Request the same ticker twice and verify the second request returns in < 100ms.
*   [ ] **Logic Test**: Test with a known "UP" trend and forced "NEGATIVE" sentiment to verify a "CONFLICTING" verdict.
