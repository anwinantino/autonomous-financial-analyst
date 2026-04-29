/**
 * components/Chart.tsx — Chart.js price forecast visualization (FR-012).
 * Stub placeholder — full implementation in FR-012 sprint.
 */

"use client";

import { PredictResponse } from "@/utils/api";

interface ChartProps {
  data: PredictResponse;
}

export default function Chart({ data }: ChartProps) {
  // TODO (FR-012): Render Chart.js Line chart with:
  //   - Historical prices line
  //   - Forecast prices line (dashed)
  //   - Confidence interval band (yhat_lower / yhat_upper)
  //   - Interactive tooltips
  //   - Responsive sizing
  return (
    <div
      id="price-chart"
      className="w-full h-64 bg-white/5 rounded-2xl flex items-center justify-center"
    >
      <p className="text-white/40 text-sm">Chart will render here — FR-012</p>
    </div>
  );
}
