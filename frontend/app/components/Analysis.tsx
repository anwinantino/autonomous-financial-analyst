/**
 * components/Analysis.tsx — News + Verdict display (FR-015, FR-016).
 * Stub placeholder — full implementation in FR-015/016 sprint.
 */

"use client";

import { AnalyzeResponse } from "@/utils/api";

interface AnalysisProps {
  data: AnalyzeResponse;
}

const VERDICT_STYLES: Record<string, string> = {
  ALIGNED: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
  CONFLICTING: "bg-red-500/20 text-red-300 border border-red-500/30",
  UNCERTAIN: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
};

export default function Analysis({ data }: AnalysisProps) {
  const verdictStyle = VERDICT_STYLES[data.verdict] ?? VERDICT_STYLES["UNCERTAIN"];

  return (
    <div id="analysis-section" className="flex flex-col gap-4 w-full">
      {/* Verdict badge */}
      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold w-fit ${verdictStyle}`}>
        <span>{data.verdict}</span>
        <span className="opacity-60">· {Math.round(data.confidence * 100)}% confidence</span>
      </div>

      {/* Reasoning */}
      <p className="text-white/70 text-sm leading-relaxed">{data.reasoning}</p>

      {/* News articles */}
      <div className="flex flex-col gap-2">
        {data.news.map((article, i) => (
          <div key={i} className="bg-white/5 rounded-xl p-3">
            <p className="text-white text-sm font-medium">{article.title}</p>
            <p className="text-white/50 text-xs mt-1">{article.snippet}</p>
            {article.source && (
              <p className="text-violet-400 text-xs mt-1">{article.source}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
