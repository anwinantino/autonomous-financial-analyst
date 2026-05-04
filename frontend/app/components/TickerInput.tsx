/**
 * components/TickerInput.tsx — Ticker input field, market selector, and Analyze button (FR-011).
 */

"use client";

interface TickerInputProps {
  value: string;
  market: string;
  onChange: (value: string) => void;
  onMarketChange: (market: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

const MARKETS = [
  { value: "US",  label: "🇺🇸 US" },
  { value: "NSE", label: "🇮🇳 NSE" },
  { value: "BSE", label: "🇮🇳 BSE" },
];

export default function TickerInput({
  value,
  market,
  onChange,
  onMarketChange,
  onSubmit,
  isLoading,
}: TickerInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading) {
      onSubmit();
    }
  };

  return (
    <div className="flex flex-col gap-3 w-full max-w-xl mx-auto">
      {/* Row 1: Market selector + ticker input */}
      <div className="flex gap-2 w-full">
        {/* Market dropdown */}
        <select
          id="market-select"
          value={market}
          onChange={(e) => onMarketChange(e.target.value)}
          disabled={isLoading}
          className="px-3 py-3.5 rounded-xl border border-white/10 bg-white/5 backdrop-blur
                     text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50
                     focus:border-violet-500/50 disabled:opacity-50 text-sm font-medium
                     transition-all duration-200 cursor-pointer appearance-none
                     min-w-[110px]"
          aria-label="Select market"
          style={{ backgroundImage: "none" }}
        >
          {MARKETS.map((m) => (
            <option
              key={m.value}
              value={m.value}
              style={{ backgroundColor: "#1a1a2e", color: "white" }}
            >
              {m.label}
            </option>
          ))}
        </select>

        {/* Ticker input */}
        <div className="relative flex-1">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/25 text-lg select-none">
            🔍
          </span>
          <input
            id="ticker-input"
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value.toUpperCase())}
            onKeyDown={handleKeyDown}
            placeholder={
              market === "NSE" || market === "BSE"
                ? "e.g. RELIANCE, TCS"
                : "e.g. AAPL, BTC-USD"
            }
            maxLength={12}
            disabled={isLoading}
            className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-white/10 bg-white/5 backdrop-blur
                       text-white placeholder-white/25 focus:outline-none focus:ring-2 focus:ring-violet-500/50
                       focus:border-violet-500/50 disabled:opacity-50 text-base font-medium transition-all duration-200"
            aria-label="Stock or crypto ticker symbol"
          />
        </div>
      </div>

      {/* Row 2: Analyze button */}
      <button
        id="analyze-button"
        onClick={onSubmit}
        disabled={isLoading || !value.trim()}
        className="btn-primary px-6 py-3.5 rounded-xl font-semibold text-base
                   bg-violet-600 hover:bg-violet-500
                   text-white shadow-lg shadow-violet-900/30
                   disabled:opacity-40 disabled:cursor-not-allowed w-full"
        aria-label="Analyze ticker"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
            </svg>
            Analyzing…
          </span>
        ) : (
          "Analyze"
        )}
      </button>
    </div>
  );
}
