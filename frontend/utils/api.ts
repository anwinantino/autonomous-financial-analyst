/**
 * utils/api.ts — API client for backend communication (FR-013, FR-015).
 *
 * All backend calls are centralized here so that:
 *  - The API base URL comes from env, never hardcoded.
 *  - Every request has a hard timeout via AbortController (FR-015).
 *  - Error handling maps HTTP status codes to user-friendly strings (FR-015).
 *  - /predict and /analyze can be called in true parallel (FR-013).
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Hard timeout per request (ms) — FR-015
const REQUEST_TIMEOUT_MS = 10_000;

// ── Response types ─────────────────────────────────────────────────────────

export interface PredictResponse {
  // Last 90 days of actual closing prices
  historical_dates: string[];
  historical_prices: number[];
  // 30-day forecast
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
  url?: string;
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
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/predict?ticker=${encodeURIComponent(ticker)}`
  );
  return handleResponse<PredictResponse>(response);
}

/**
 * Fetches news sentiment analysis and alignment verdict for a ticker.
 * FR-013: trend is now OPTIONAL — omit to allow true parallel execution with /predict.
 * Target response time: 3–6 seconds (FR-008).
 */
export async function fetchAnalysis(
  ticker: string,
  trend?: string
): Promise<AnalyzeResponse> {
  const url = trend
    ? `${API_BASE_URL}/analyze?ticker=${encodeURIComponent(ticker)}&trend=${trend}`
    : `${API_BASE_URL}/analyze?ticker=${encodeURIComponent(ticker)}`;

  const response = await fetchWithTimeout(url);
  return handleResponse<AnalyzeResponse>(response);
}

// ── Internal helpers ───────────────────────────────────────────────────────

/**
 * Wraps fetch() with an AbortController timeout (FR-015).
 * Throws a user-friendly error if the request exceeds REQUEST_TIMEOUT_MS.
 */
async function fetchWithTimeout(url: string): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, { signal: controller.signal });
    return response;
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request took too long. Please try again.");
    }
    // Network-level failure (no internet, server down)
    throw new Error("Connection failed. Check your internet connection.");
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Centralized response handler that maps HTTP errors to user-friendly messages (FR-015).
 * Never exposes raw server error strings to the UI.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 404) {
    throw new Error("Ticker not found. Please check the spelling and try again.");
  }
  if (response.status === 422) {
    throw new Error(
      "Invalid ticker format. Use alphanumeric characters only (e.g. AAPL, BTC-USD)."
    );
  }
  if (response.status === 502) {
    throw new Error("News retrieval failed. Please try again in a moment.");
  }
  if (response.status === 503 || response.status === 504) {
    throw new Error("The server is currently unavailable. Please try again shortly.");
  }
  if (!response.ok) {
    throw new Error("Request failed. Please try again.");
  }
  return response.json() as Promise<T>;
}
