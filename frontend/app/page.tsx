/**
 * app/page.tsx — Main dashboard page (FR-011 through FR-015).
 *
 * FR-013: /predict and /analyze fire simultaneously — neither blocks the other.
 * FR-014: Separate loading states per section, debounce via in-flight ref.
 * FR-015: Partial failures are isolated — a failed analysis never hides a chart.
 */

"use client";

import { useState, useRef } from "react";
import TickerInput from "./components/TickerInput";
import Chart from "./components/Chart";
import Analysis from "./components/Analysis";
import LoadingSpinner from "./components/LoadingSpinner";
import { fetchPrediction, fetchAnalysis, PredictResponse, AnalyzeResponse } from "@/utils/api";

export default function HomePage() {
  const [ticker, setTicker] = useState("");
  const [market, setMarket] = useState("US");

  // ── Per-section data ────────────────────────────────────────────────────
  const [predictData, setPredictData] = useState<PredictResponse | null>(null);
  const [analyzeData, setAnalyzeData] = useState<AnalyzeResponse | null>(null);

  // ── Per-section loading (FR-014) ────────────────────────────────────────
  const [isPredicting, setIsPredicting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // ── Per-section errors (FR-015) ─────────────────────────────────────────
  const [predictError, setPredictError] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  // ── Debounce guard (FR-014) ─────────────────────────────────────────────
  // Tracks the current "run ID" so stale responses from cancelled requests
  // are silently dropped rather than updating state.
  const runIdRef = useRef(0);

  const handleAnalyze = () => {
    const cleanTicker = ticker.trim().toUpperCase();
    if (!cleanTicker || isPredicting || isAnalyzing) return;

    // Increment run ID — any in-flight callbacks from previous runs will be ignored
    const runId = ++runIdRef.current;

    // Reset all state for the new query
    setPredictData(null);
    setAnalyzeData(null);
    setPredictError(null);
    setAnalyzeError(null);
    setIsPredicting(true);
    setIsAnalyzing(true);

    // ── FR-013 UPDATE: /predict first, then /analyze with the real trend ───
    // /analyze needs the ML trend to give an accurate verdict.
    // Calling both in true parallel caused /analyze to always receive NEUTRAL
    // (the backend default), making the LLM comparison meaningless.
    // Fix: fire /predict, update the chart immediately, then fire /analyze
    // with the resolved trend. Analyse loading state starts upfront so the
    // spinner shows from the beginning.

    // /predict — chart section
    fetchPrediction(cleanTicker, market)
      .then((data) => {
        if (runId !== runIdRef.current) return; // stale — discard
        setPredictData(data);

        // Now fire /analyze with the REAL trend from the ML model
        fetchAnalysis(cleanTicker, data.trend, market)
          .then((analyzeResult) => {
            if (runId !== runIdRef.current) return;
            setAnalyzeData(analyzeResult);
          })
          .catch((err: Error) => {
            if (runId !== runIdRef.current) return;
            setAnalyzeError(err.message);
          })
          .finally(() => {
            if (runId !== runIdRef.current) return;
            setIsAnalyzing(false);
          });
      })
      .catch((err: Error) => {
        if (runId !== runIdRef.current) return;
        setPredictError(err.message);
        // Predict failed — still try /analyze without a trend (graceful degradation)
        fetchAnalysis(cleanTicker, undefined, market)
          .then((analyzeResult) => {
            if (runId !== runIdRef.current) return;
            setAnalyzeData(analyzeResult);
          })
          .catch((analyzeErr: Error) => {
            if (runId !== runIdRef.current) return;
            setAnalyzeError(analyzeErr.message);
          })
          .finally(() => {
            if (runId !== runIdRef.current) return;
            setIsAnalyzing(false);
          });
      })
      .finally(() => {
        if (runId !== runIdRef.current) return;
        setIsPredicting(false);
      });
  };

  const isLoading = isPredicting || isAnalyzing;
  const hasResults =
    isPredicting || isAnalyzing ||
    predictData || analyzeData ||
    predictError || analyzeError;

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
          market={market}
          onChange={setTicker}
          onMarketChange={setMarket}
          onSubmit={handleAnalyze}
          isLoading={isLoading}
        />

        {/* ── Results Grid ─────────────────────────────────────────────── */}
        {hasResults && (
          <div className="flex flex-col gap-6">

            {/* Predict section (FR-014: independent spinner) */}
            {isPredicting && (
              <LoadingSpinner message="Generating forecast (waking up server...)" />
            )}
            {/* FR-015: Isolated predict error — analysis section still shows */}
            {predictError && !isPredicting && (
              <div
                id="predict-error"
                className="glass p-4 text-red-400 border-red-500/20 text-sm flex items-start gap-3 fade-up"
              >
                <span className="text-xl mt-0.5">⚠️</span>
                <div>
                  <p className="font-semibold">Forecast unavailable</p>
                  <p className="text-red-400/70 mt-0.5">{predictError}</p>
                </div>
              </div>
            )}
            {predictData && !isPredicting && <Chart data={predictData} market={market} />}

            {/* Analyze section (FR-014: independent spinner) */}
            {isAnalyzing && (
              <LoadingSpinner message="Running AI analysis (fetching news...)" />
            )}
            {/* FR-015: Isolated analyze error — chart still shows */}
            {analyzeError && !isAnalyzing && (
              <div
                id="analyze-error"
                className="glass p-4 text-amber-400 border-amber-500/20 text-sm flex items-start gap-3 fade-up"
              >
                <span className="text-xl mt-0.5">🔍</span>
                <div>
                  <p className="font-semibold">Analysis unavailable</p>
                  <p className="text-amber-400/70 mt-0.5">{analyzeError}</p>
                </div>
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
