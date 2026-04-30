/**
 * components/ForecastChart.tsx — FR-012: Combined historical + forecast chart.
 *
 * Layout:
 *  LEFT  → Last 90 days of ACTUAL closing prices (solid white line)
 *  RIGHT → 30-day PROPHET FORECAST (dashed violet line)
 *  BAND  → Confidence interval (upper/lower bounds, violet fill) over forecast only
 *
 * A vertical "Today" annotation separates the two segments visually.
 */

"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  type ChartOptions,
  type ChartData,
  type Plugin,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { PredictResponse } from "@/utils/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface ForecastChartProps {
  data: PredictResponse;
}

// ── "Today" vertical line plugin ──────────────────────────────────────────
// Draws a vertical divider between historical and forecast zones.
const todayLinePlugin: Plugin<"line"> = {
  id: "todayLine",
  afterDraw(chart) {
    const meta = chart.getDatasetMeta(0); // historical dataset
    if (!meta.data.length) return;

    const lastHistoricalPoint = meta.data[meta.data.length - 1];
    if (!lastHistoricalPoint) return;

    const { ctx, chartArea } = chart;
    const x = lastHistoricalPoint.x;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(x, chartArea.top);
    ctx.lineTo(x, chartArea.bottom);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.stroke();

    // "Today" label
    ctx.fillStyle = "rgba(255, 255, 255, 0.25)";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Today", x, chartArea.top - 6);
    ctx.restore();
  },
};

export default function ForecastChart({ data }: ForecastChartProps) {
  const {
    historical_dates,
    historical_prices,
    dates,
    prices,
    lower_bound,
    upper_bound,
    trend,
    current_price,
  } = data;

  const trendColor =
    trend === "UP" ? "#34d399" : trend === "DOWN" ? "#f87171" : "#94a3b8";

  // ── Merge labels: history + forecast ─────────────────────────────────────
  // The historical section occupies indices 0..H-1
  // The forecast section occupies indices H..H+F-1
  const H = historical_dates.length;
  const allLabels = [...historical_dates, ...dates];

  // ── Dataset 1: Historical actuals ─────────────────────────────────────────
  // Solid white/slate line for the left portion, null for the forecast zone.
  const historicalData: (number | null)[] = [
    ...historical_prices,
    ...Array(dates.length).fill(null),
  ];

  // ── Dataset 2: Upper bound (invisible, used for fill reference) ───────────
  const upperData: (number | null)[] = [
    ...Array(H).fill(null),
    ...upper_bound,
  ];

  // ── Dataset 3: Lower bound (invisible, fills down to here from upper) ─────
  const lowerData: (number | null)[] = [
    ...Array(H).fill(null),
    ...lower_bound,
  ];

  // ── Dataset 4: Forecast line ──────────────────────────────────────────────
  // Null for the history zone, then the prophet yhat values.
  // We bridge the gap by adding the last historical price at index H-1.
  const forecastData: (number | null)[] = [
    ...Array(H - 1).fill(null),
    historical_prices[H - 1], // bridge point = last known actual
    ...prices,
  ];

  const chartData: ChartData<"line"> = {
    labels: allLabels,
    datasets: [
      // 1. Historical actual prices
      {
        label: "Historical Price",
        data: historicalData,
        borderColor: "rgba(255, 255, 255, 0.75)",
        backgroundColor: "transparent",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: "rgba(255,255,255,0.9)",
        tension: 0.25,
        spanGaps: false,
        order: 1,
      },
      // 2. Upper confidence bound (fill reference, legend-hidden)
      {
        label: "Upper Bound",
        data: upperData,
        borderColor: "transparent",
        backgroundColor: "rgba(139, 92, 246, 0.10)",
        pointRadius: 0,
        fill: "+1", // fills down to Lower Bound dataset (index 3)
        tension: 0.35,
        spanGaps: false,
        order: 4,
      },
      // 3. Lower confidence bound
      {
        label: "Confidence Band",
        data: lowerData,
        borderColor: "transparent",
        backgroundColor: "rgba(139, 92, 246, 0.10)",
        pointRadius: 0,
        fill: false,
        tension: 0.35,
        spanGaps: false,
        order: 5,
      },
      // 4. Prophet forecast line
      {
        label: "30-Day Forecast",
        data: forecastData,
        borderColor: "#8b5cf6",
        backgroundColor: "transparent",
        borderWidth: 2.5,
        borderDash: [6, 4],
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#8b5cf6",
        tension: 0.35,
        spanGaps: false,
        order: 2,
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: true,
    layout: { padding: { top: 16 } }, // room for "Today" label
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top",
        align: "end",
        labels: {
          color: "rgba(255,255,255,0.45)",
          boxWidth: 14,
          usePointStyle: true,
          pointStyle: "line",
          font: { size: 11, family: "Inter, sans-serif" },
          filter: (item) =>
            item.text !== "Upper Bound" && item.text !== "Confidence Band",
        },
      },
      tooltip: {
        backgroundColor: "rgba(2, 6, 23, 0.92)",
        borderColor: "rgba(139, 92, 246, 0.35)",
        borderWidth: 1,
        titleColor: "rgba(255,255,255,0.85)",
        bodyColor: "rgba(255,255,255,0.55)",
        padding: 12,
        displayColors: false,
        callbacks: {
          title: (items) => items[0]?.label ?? "",
          label: (ctx) => {
            if (ctx.raw === null) return "";
            const val = `$${Number(ctx.raw).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            if (ctx.dataset.label === "Historical Price")
              return `  Actual    ${val}`;
            if (ctx.dataset.label === "30-Day Forecast")
              return `  Forecast  ${val}`;
            if (ctx.dataset.label === "Confidence Band")
              return `  Low       ${val}`;
            if (ctx.dataset.label === "Upper Bound")
              return `  High      ${val}`;
            return "";
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "rgba(255,255,255,0.25)",
          maxTicksLimit: 7,
          maxRotation: 0,
          font: { size: 10, family: "Inter, sans-serif" },
        },
        grid: { color: "rgba(255,255,255,0.04)" },
        border: { color: "transparent" },
      },
      y: {
        ticks: {
          color: "rgba(255,255,255,0.25)",
          maxTicksLimit: 5,
          font: { size: 10, family: "Inter, sans-serif" },
          callback: (val) =>
            `$${Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
        },
        grid: { color: "rgba(255,255,255,0.04)" },
        border: { color: "transparent" },
      },
    },
  };

  return (
    <div id="price-chart" className="glass glass-hover p-5 fade-up overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <p className="text-white/35 text-xs uppercase tracking-widest">
            90-Day History + 30-Day Forecast
          </p>
          <p className="text-white text-2xl font-bold mt-0.5">
            ${current_price.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
            <span className="text-white/30 text-sm font-normal ml-1">current</span>
          </p>
        </div>
        <span
          className="px-3 py-1 rounded-full text-xs font-semibold tracking-wider"
          style={{
            background: `${trendColor}22`,
            color: trendColor,
            border: `1px solid ${trendColor}44`,
          }}
        >
          {trend === "UP" ? "↑" : trend === "DOWN" ? "↓" : "–"} {trend}
        </span>
      </div>

      {/* Chart */}
      <div className="w-full overflow-hidden">
        <Line data={chartData} options={options} plugins={[todayLinePlugin]} />
      </div>

      {/* Legend hint */}
      <div className="flex items-center gap-4 mt-3 px-1">
        <div className="flex items-center gap-1.5">
          <span className="w-5 h-0.5 bg-white/60 rounded-full inline-block" />
          <span className="text-white/30 text-xs">Actual</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className="w-5 h-0.5 rounded-full inline-block"
            style={{ background: "#8b5cf6", borderTop: "2px dashed #8b5cf6", height: 0 }}
          />
          <span className="text-white/30 text-xs">Forecast</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className="w-5 h-2.5 rounded-sm inline-block"
            style={{ background: "rgba(139,92,246,0.2)" }}
          />
          <span className="text-white/30 text-xs">Confidence Band</span>
        </div>
      </div>
    </div>
  );
}
