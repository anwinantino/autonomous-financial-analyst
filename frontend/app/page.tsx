/**
 * app/page.tsx — Main dashboard page (FR-011, FR-012, FR-013).
 *
 * Orchestrates:
 *  1. Ticker input + form submission
 *  2. Parallel /predict and /analyze API calls (FR-013)
 *  3. Graph renders immediately when /predict returns
 *  4. Analysis section updates when /analyze returns
 *  5. Per-section loading states and error handling (FR-014, FR-015)
 */

"use client";

import { useState } from "react";
import TickerInput from "./components/TickerInput";
import Chart from "./components/Chart";
import Analysis from "./components/Analysis";
import LoadingSpinner from "./components/LoadingSpinner";
import { fetchPrediction, fetchAnalysis, PredictResponse, AnalyzeResponse } from "@/utils/api";

export default function HomePage() {
  const [ticker, setTicker] = useState("");
  const [predictData, setPredictData] = useState<PredictResponse | null>(null);
  const [analyzeData, setAnalyzeData] = useState<AnalyzeResponse | null>(null);

  const [isPredicting, setIsPredicting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [predictError, setPredictError] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    const cleanTicker = ticker.trim().toUpperCase();
    if (!cleanTicker || isPredicting) return;

    // Reset state before new requests
    setPredictData(null);
    setAnalyzeData(null);
    setPredictError(null);
    setAnalyzeError(null);
    setIsPredicting(true);
    setIsAnalyzing(true);

    // ── Parallel API calls (FR-013) ───────────────────────────────────────
    // /predict and /analyze fire simultaneously.
    // The graph renders as soon as /predict resolves,
    // without waiting for the slower /analyze call.

    const predictPromise = fetchPrediction(cleanTicker)
      .then((data) => {
        setPredictData(data);
        return data;
      })
      .catch((err: Error) => {
        setPredictError(err.message);
        return null;
      })
      .finally(() => setIsPredicting(false));

    const analyzePromise = predictPromise.then((prediction) => {
      // Pass the trend from /predict to /analyze to enable comparator logic
      const trend = prediction?.trend ?? "NEUTRAL";
      return fetchAnalysis(cleanTicker, trend)
        .then((data) => setAnalyzeData(data))
        .catch((err: Error) => setAnalyzeError(err.message))
        .finally(() => setIsAnalyzing(false));
    });

    // Suppress unhandled rejection warnings — errors are caught above
    void analyzePromise;
  };

  const isLoading = isPredicting || isAnalyzing;

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-violet-950 to-slate-900 px-4 py-12">
      <div className="max-w-2xl mx-auto flex flex-col gap-10">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white tracking-tight">
            Autonomous Financial Analyst
          </h1>
          <p className="mt-2 text-white/50 text-sm">
            ML price forecast · AI news validation · Alignment verdict
          </p>
        </div>

        {/* Ticker Input */}
        <TickerInput
          value={ticker}
          onChange={setTicker}
          onSubmit={handleAnalyze}
          isLoading={isLoading}
        />

        {/* Predict Section */}
        {isPredicting && <LoadingSpinner message="Fetching prediction…" />}
        {predictError && (
          <div
            id="predict-error"
            className="text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm"
          >
            {predictError}
          </div>
        )}
        {predictData && !isPredicting && <Chart data={predictData} />}

        {/* Analyze Section */}
        {isAnalyzing && <LoadingSpinner message="Analyzing news sentiment…" />}
        {analyzeError && (
          <div
            id="analyze-error"
            className="text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3 text-sm"
          >
            {analyzeError}
          </div>
        )}
        {analyzeData && !isAnalyzing && <Analysis data={analyzeData} />}

        {/* Disclaimer */}
        <footer className="text-center text-white/25 text-xs mt-4">
          ⚠️ Not financial advice. For educational purposes only.
        </footer>
      </div>
    </main>
  );
}
