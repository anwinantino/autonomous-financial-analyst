/**
 * components/Analysis.tsx — News sentiment + Verdict display (FR-016).
 *
 * FR-016: Color-coded verdict badge (Green/Red/Yellow) with:
 *  - SVG confidence ring showing score visually
 *  - Percentage confidence label
 *  - Staggered fade-up animation for news cards
 *  - Hover effects on each news card
 */

"use client";

import { AnalyzeResponse } from "@/utils/api";

interface AnalysisProps {
  data: AnalyzeResponse;
}

// ── Verdict configuration ──────────────────────────────────────────────────
const VERDICT_CONFIG: Record<
  string,
  { label: string; icon: string; bg: string; text: string; border: string; ringBg: string }
> = {
  ALIGNED: {
    label: "ALIGNED",
    icon: "✓",
    bg: "rgba(52,211,153,0.12)",
    text: "#34d399",
    border: "rgba(52,211,153,0.30)",
    ringBg: "rgba(52,211,153,0.08)",
  },
  CONFLICTING: {
    label: "CONFLICTING",
    icon: "✕",
    bg: "rgba(248,113,113,0.12)",
    text: "#f87171",
    border: "rgba(248,113,113,0.30)",
    ringBg: "rgba(248,113,113,0.08)",
  },
  UNCERTAIN: {
    label: "UNCERTAIN",
    icon: "?",
    bg: "rgba(251,191,36,0.12)",
    text: "#fbbf24",
    border: "rgba(251,191,36,0.30)",
    ringBg: "rgba(251,191,36,0.08)",
  },
};

// Stagger classes for news cards
const STAGGER = ["fade-up-1", "fade-up-2", "fade-up-3", "fade-up-4", "fade-up-5"];

// ── SVG Confidence Ring ────────────────────────────────────────────────────
function ConfidenceRing({
  value,
  color,
}: {
  value: number; // 0.0 – 1.0
  color: string;
}) {
  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const filled = circumference * value;
  const gap = circumference - filled;

  return (
    <svg width="44" height="44" viewBox="0 0 44 44" className="flex-shrink-0" aria-hidden>
      {/* Background track */}
      <circle
        cx="22"
        cy="22"
        r={radius}
        fill="none"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="3"
      />
      {/* Filled arc */}
      <circle
        cx="22"
        cy="22"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="3"
        strokeDasharray={`${filled} ${gap}`}
        strokeLinecap="round"
        transform="rotate(-90 22 22)"
        style={{ transition: "stroke-dasharray 0.6s ease" }}
      />
      {/* Icon in centre */}
      <text
        x="22"
        y="27"
        textAnchor="middle"
        fill={color}
        fontSize="13"
        fontWeight="700"
        fontFamily="Inter, sans-serif"
      >
        {value >= 0.7 ? "✓" : value <= 0.45 ? "?" : "!"}
      </text>
    </svg>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────
export default function Analysis({ data }: AnalysisProps) {
  const cfg = VERDICT_CONFIG[data.verdict] ?? VERDICT_CONFIG["UNCERTAIN"];
  const pct = Math.round(data.confidence * 100);

  return (
    <div id="analysis-section" className="flex flex-col gap-5 w-full fade-up">

      {/* ── Verdict card (FR-016) ─────────────────────────────────────── */}
      <div
        className="glass p-5 flex items-start gap-4"
        style={{ borderColor: cfg.border, background: cfg.ringBg }}
      >
        {/* SVG confidence ring */}
        <ConfidenceRing value={data.confidence} color={cfg.text} />

        <div className="flex-1 min-w-0">
          {/* Verdict label + confidence pill */}
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-sm font-bold tracking-widest uppercase"
              style={{ color: cfg.text }}
            >
              {cfg.label}
            </span>

            {/* Confidence score pill (FR-016) */}
            <span
              className="px-2 py-0.5 rounded-full text-xs font-semibold"
              style={{
                background: cfg.bg,
                color: cfg.text,
                border: `1px solid ${cfg.border}`,
              }}
            >
              {pct}% confidence
            </span>

            {/* Sentiment tag */}
            <span className="text-white/25 text-xs hidden sm:inline">
              · {data.sentiment}
            </span>
          </div>

          {/* AI reasoning */}
          <p className="text-white/55 text-sm leading-relaxed mt-2">{data.reasoning}</p>
        </div>
      </div>

      {/* ── News cards ───────────────────────────────────────────────── */}
      {data.news.length > 0 && (
        <div>
          <p className="text-white/25 text-xs uppercase tracking-widest mb-3 px-1">
            Latest News · {data.news.length} articles
          </p>
          <div className="flex flex-col gap-2">
            {data.news.map((article, i) => (
              <div
                key={i}
                className={`glass glass-hover p-4 cursor-default ${STAGGER[i] ?? "fade-up"}`}
              >
                <p className="text-white text-sm font-semibold leading-snug line-clamp-2">
                  {article.title}
                </p>
                <p className="text-white/40 text-xs mt-1.5 leading-relaxed line-clamp-2">
                  {article.snippet}
                </p>
                {article.source && (
                  <p className="text-violet-400/60 text-xs mt-2 font-medium">
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
