# Implementation Plan: FR-013, FR-014, FR-015 (Asynchronous Logic & Error Handling)

This plan focuses on the complex state management required to handle parallel API requests, specific loading states, and user-friendly error recovery.

---

## 1. FR-013: Parallel API Calls
**Goal**: Launch `/predict` and `/analyze` simultaneously to minimize total wait time and allow the graph to render independently.

### Technical Tasks
*   [ ] **Backend Adjustment (Prerequisite)**:
    *   Update `/analyze` in `backend/app/routes/analyze.py` to make the `trend` parameter optional.
    *   If `trend` is missing, `/analyze` will fetch it from the cached Prophet model internally.
*   [ ] **Frontend Logic**:
    *   Refactor `handleAnalyze` in `page.tsx` to fire both `fetchPrediction` and `fetchAnalysis` at the exact same time using independent promise chains (not nested).
    *   Ensure the Graph mounts immediately upon `predictData` resolution, regardless of whether `analyzeData` is still pending.

---

## 2. FR-014: Granular Loading States
**Goal**: Provide per-component feedback to the user and prevent duplicate submissions.

### Technical Tasks
*   [ ] **State Separation**:
    *   `predictLoading`: Specifically for the forecast graph.
    *   `analyzeLoading`: Specifically for the AI sentiment section.
*   [ ] **Input Protection**:
    *   Disable the "Analyze" button and ticker input field if `predictLoading || analyzeLoading` is true.
*   [ ] **Visual Feedback**:
    *   Update `LoadingSpinner` usage to show distinct messages: "Generating 30-day forecast..." and "Running AI sentiment analysis...".

---

## 3. FR-015: User-Friendly Error Handling
**Goal**: Prevent raw code errors from reaching the user and handle partial failures gracefully.

### Technical Tasks
*   [ ] **API Helper Enhancement (`utils/api.ts`)**:
    *   Implement `AbortController` with a **10-second timeout** for all fetch calls.
    *   Expand `handleResponse` to map status codes to the specific strings requested in the FR (e.g., "Ticker not found. Please check spelling.").
*   [ ] **Partial Failure Support**:
    *   If one call fails but the other succeeds, the UI should still render the successful part.
    *   Implement small, styled error banners within the component's reserved space for the failed part.

---

## 4. Verification & Testing
*   [ ] **Network Throttling**: Test in browser dev tools (Slow 3G) to verify the graph loads while the analysis continues to spin.
*   [ ] **Error Triggering**: Test with `INVALID-TKR` and verify the custom message appears.
*   [ ] **Concurrency Test**: Double-click the "Analyze" button quickly to ensure only one set of requests is processed.
