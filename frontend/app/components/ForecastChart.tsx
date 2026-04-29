/**
 * components/ForecastChart.tsx — FR-012: Chart.js price forecast visualization.
 *
 * Renders:
 *  - Forecast price line (dashed violet)
 *  - Confidence interval band (semi-transparent fill between lower/upper bounds)
 *  - Interactive tooltips with price + date
 *  - Responsive sizing
 *  - Legend distinguishing data types
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
} from "chart.js";
import { Line } from "react-chartjs-2";
import { PredictResponse } from "@/utils/api";

// Register all required Chart.js modules
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

export default function ForecastChart({ data }: ForecastChartProps) {
  const { dates, prices, lower_bound, upper_bound, trend, current_price } = data;

  // Trend badge colour
  const trendColor =
    trend === "UP"
      ? "#34d399"
      : trend === "DOWN"
      ? "#f87171"
      : "#94a3b8";

  const chartData: ChartData<"line"> = {
    labels: dates,
    datasets: [
      // ── Upper confidence bound (transparent, used for fill reference) ──
      {
        label: "Upper Bound",
        data: upper_bound,
        borderColor: "transparent",
        backgroundColor: "rgba(139, 92, 246, 0.08)",
        pointRadius: 0,
        fill: "+1", // fill down to Lower Bound dataset
        tension: 0.35,
        order: 3,
      },
      // ── Lower confidence bound ───────────────────────────────────────
      {
        label: "Confidence Interval",
        data: lower_bound,
        borderColor: "transparent",
        backgroundColor: "rgba(139, 92, 246, 0.08)",
        pointRadius: 0,
        fill: false,
        tension: 0.35,
        order: 4,
      },
      // ── Forecast price line ──────────────────────────────────────────
      {
        label: "30-Day Forecast",
        data: prices,
        borderColor: "#8b5cf6",
        backgroundColor: "rgba(139, 92, 246, 0.0)",
        borderWidth: 2.5,
        borderDash: [6, 4],
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#8b5cf6",
        tension: 0.35,
        order: 1,
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: true,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top",
        align: "end",
        labels: {
          color: "rgba(255,255,255,0.5)",
          boxWidth: 14,
          usePointStyle: true,
          pointStyle: "line",
          font: { size: 12, family: "Inter, sans-serif" },
          filter: (item) =>
            // Hide the "Upper Bound" raw dataset from the legend
            item.text !== "Upper Bound",
        },
      },
      tooltip: {
        backgroundColor: "rgba(2, 6, 23, 0.92)",
        borderColor: "rgba(139, 92, 246, 0.4)",
        borderWidth: 1,
        titleColor: "rgba(255,255,255,0.9)",
        bodyColor: "rgba(255,255,255,0.6)",
        padding: 12,
        displayColors: false,
        callbacks: {
          title: (items) => items[0]?.label ?? "",
          label: (ctx) => {
            if (ctx.dataset.label === "30-Day Forecast")
              return `  Forecast  $${Number(ctx.raw).toFixed(2)}`;
            if (ctx.dataset.label === "Confidence Interval")
              return `  Low       $${Number(ctx.raw).toFixed(2)}`;
            if (ctx.dataset.label === "Upper Bound")
              return `  High      $${Number(ctx.raw).toFixed(2)}`;
            return "";
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "rgba(255,255,255,0.3)",
          maxTicksLimit: 6,
          font: { size: 11, family: "Inter, sans-serif" },
        },
        grid: { color: "rgba(255,255,255,0.04)" },
        border: { color: "transparent" },
      },
      y: {
        ticks: {
          color: "rgba(255,255,255,0.3)",
          maxTicksLimit: 5,
          font: { size: 11, family: "Inter, sans-serif" },
          callback: (val) => `$${Number(val).toLocaleString()}`,
        },
        grid: { color: "rgba(255,255,255,0.04)" },
        border: { color: "transparent" },
      },
    },
  };

  return (
    <div id="price-chart" className="glass p-5 fade-up">
      {/* Chart header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-white/40 text-xs uppercase tracking-widest">30-Day Forecast</p>
          <p className="text-white text-2xl font-bold mt-0.5">
            ${current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
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

      {/* Chart canvas */}
      <Line data={chartData} options={options} />
    </div>
  );
}
