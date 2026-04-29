/**
 * utils/api.ts — API client for backend communication (FR-013, FR-015).
 *
 * All backend calls are centralized here so that:
 *  - The API base URL comes from env, never hardcoded.
 *  - Error handling is uniform across all calls.
 *  - Both /predict and /analyze can be called in parallel.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Response types ─────────────────────────────────────────────────────────

export interface PredictResponse {
  dates: string[];
  prices: number[];
  lower_bound: number[];
  upper_bound: number[];
  trend: "UP" | "DOWN" | "NEUTRAL";
  current_price: number;
}

export interface NewsArticle {
  title: string;
  snippet: string;
  source?: string;
}

export interface AnalyzeResponse {
  news: NewsArticle[];
  sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL";
  verdict: "ALIGNED" | "CONFLICTING" | "UNCERTAIN";
  confidence: number;
  reasoning: string;
}

// ── API calls ──────────────────────────────────────────────────────────────

/**
 * Fetches the 30-day price forecast for a given ticker.
 * Target response time: < 2 seconds (FR-007).
 */
export async function fetchPrediction(ticker: string): Promise<PredictResponse> {
  const response = await fetch(
    `${API_BASE_URL}/predict?ticker=${encodeURIComponent(ticker)}`
  );
  return handleResponse<PredictResponse>(response);
}

/**
 * Fetches news sentiment analysis and alignment verdict for a ticker.
 * Target response time: 3–6 seconds (FR-008).
 */
export async function fetchAnalysis(
  ticker: string,
  trend: string
): Promise<AnalyzeResponse> {
  const response = await fetch(
    `${API_BASE_URL}/analyze?ticker=${encodeURIComponent(ticker)}&trend=${trend}`
  );
  return handleResponse<AnalyzeResponse>(response);
}

// ── Internal helpers ───────────────────────────────────────────────────────

/**
 * Centralized response handler that maps HTTP errors to user-friendly messages.
 * Never exposes raw server error strings to the UI.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 404) {
    throw new Error("Ticker not found. Please check the spelling and try again.");
  }
  if (response.status === 422) {
    throw new Error("Invalid ticker format. Use alphanumeric characters only (e.g. AAPL, BTC-USD).");
  }
  if (response.status === 502) {
    throw new Error("News retrieval failed. Please try again in a moment.");
  }
  if (!response.ok) {
    throw new Error("Request failed. Please try again.");
  }
  return response.json() as Promise<T>;
}
