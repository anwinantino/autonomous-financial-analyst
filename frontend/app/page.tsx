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
      const trend = prediction?.trend ?? "NEUTRAL";
      return fetchAnalysis(cleanTicker, trend)
        .then((data) => setAnalyzeData(data))
        .catch((err: Error) => setAnalyzeError(err.message))
        .finally(() => setIsAnalyzing(false));
    });

    void analyzePromise;
  };

  const isLoading = isPredicting || isAnalyzing;
  const hasResults = predictData || analyzeData || predictError || analyzeError;

  return (
    <main className="relative min-h-screen px-4 py-16 z-10">
      <div className="max-w-2xl mx-auto flex flex-col gap-10">

        {/* ── Header ──────────────────────────────────────────────────── */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-medium tracking-wide mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
            ML + AI · Prophet + Gemini
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white tracking-tight leading-tight">
            Autonomous<br />Financial Analyst
          </h1>
          <p className="text-white/40 text-sm max-w-sm mx-auto leading-relaxed">
            Enter a ticker to get an ML price forecast, then see if the latest news agrees.
          </p>
        </div>

        {/* ── Ticker Input ─────────────────────────────────────────────── */}
        <TickerInput
          value={ticker}
          onChange={setTicker}
          onSubmit={handleAnalyze}
          isLoading={isLoading}
        />

        {/* ── Results ──────────────────────────────────────────────────── */}
        {hasResults && (
          <div className="flex flex-col gap-6">

            {/* Predict section */}
            {isPredicting && <LoadingSpinner message="Generating 30-day forecast…" />}
            {predictError && (
              <div
                id="predict-error"
                className="glass p-4 text-red-400 border-red-500/20 text-sm flex items-center gap-3"
              >
                <span className="text-lg">⚠️</span>
                {predictError}
              </div>
            )}
            {predictData && !isPredicting && <Chart data={predictData} />}

            {/* Analyze section */}
            {isAnalyzing && <LoadingSpinner message="Analyzing news sentiment with Gemini…" />}
            {analyzeError && (
              <div
                id="analyze-error"
                className="glass p-4 text-amber-400 border-amber-500/20 text-sm flex items-center gap-3"
              >
                <span className="text-lg">🔍</span>
                {analyzeError}
              </div>
            )}
            {analyzeData && !isAnalyzing && <Analysis data={analyzeData} />}
          </div>
        )}

        {/* ── Disclaimer ───────────────────────────────────────────────── */}
        <footer className="text-center text-white/20 text-xs leading-relaxed mt-4 space-y-1">
          <p>⚠️ Not financial advice. For educational purposes only.</p>
          <p>Forecasts are generated by Prophet ML and validated by Gemini AI.</p>
        </footer>

      </div>
    </main>
  );
}
