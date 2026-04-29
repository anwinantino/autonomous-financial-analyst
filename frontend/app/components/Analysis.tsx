/**
 * components/Analysis.tsx — News sentiment + Verdict display (FR-011, FR-016).
 */

"use client";

import { AnalyzeResponse } from "@/utils/api";

interface AnalysisProps {
  data: AnalyzeResponse;
}

const VERDICT_CONFIG: Record<string, { label: string; icon: string; bg: string; text: string; border: string }> = {
  ALIGNED: {
    label: "ALIGNED",
    icon: "✓",
    bg: "rgba(52,211,153,0.1)",
    text: "#34d399",
    border: "rgba(52,211,153,0.25)",
  },
  CONFLICTING: {
    label: "CONFLICTING",
    icon: "✕",
    bg: "rgba(248,113,113,0.1)",
    text: "#f87171",
    border: "rgba(248,113,113,0.25)",
  },
  UNCERTAIN: {
    label: "UNCERTAIN",
    icon: "?",
    bg: "rgba(251,191,36,0.1)",
    text: "#fbbf24",
    border: "rgba(251,191,36,0.25)",
  },
};

export default function Analysis({ data }: AnalysisProps) {
  const cfg = VERDICT_CONFIG[data.verdict] ?? VERDICT_CONFIG["UNCERTAIN"];

  return (
    <div id="analysis-section" className="flex flex-col gap-5 w-full fade-up">

      {/* ── Verdict card ─────────────────────────────────────────────── */}
      <div
        className="glass p-5 flex items-start gap-4"
        style={{ borderColor: cfg.border }}
      >
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-lg font-bold"
          style={{ background: cfg.bg, color: cfg.text }}
        >
          {cfg.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <span
              className="text-sm font-bold tracking-widest uppercase"
              style={{ color: cfg.text }}
            >
              {cfg.label}
            </span>
            <span className="text-white/30 text-xs">
              {Math.round(data.confidence * 100)}% confidence · {data.sentiment}
            </span>
          </div>
          <p className="text-white/60 text-sm leading-relaxed mt-2">{data.reasoning}</p>
        </div>
      </div>

      {/* ── News articles ─────────────────────────────────────────────── */}
      {data.news.length > 0 && (
        <div>
          <p className="text-white/30 text-xs uppercase tracking-widest mb-3">Latest News</p>
          <div className="flex flex-col gap-2">
            {data.news.map((article, i) => (
              <div key={i} className="glass p-4 hover:border-white/15 transition-colors">
                <p className="text-white text-sm font-semibold leading-snug line-clamp-2">
                  {article.title}
                </p>
                <p className="text-white/40 text-xs mt-1.5 leading-relaxed line-clamp-2">
                  {article.snippet}
                </p>
                {article.source && (
                  <p className="text-violet-400/70 text-xs mt-2 font-medium">
                    {article.source}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
