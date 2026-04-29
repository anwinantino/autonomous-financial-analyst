/**
 * components/TickerInput.tsx — Ticker input field and Analyze button (FR-011).
 */

"use client";

interface TickerInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export default function TickerInput({ value, onChange, onSubmit, isLoading }: TickerInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading) {
      onSubmit();
    }
  };

  return (
    <div className="flex gap-3 w-full max-w-xl mx-auto">
      <div className="relative flex-1">
        {/* Search icon */}
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/25 text-lg select-none">
          🔍
        </span>
        <input
          id="ticker-input"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value.toUpperCase())}
          onKeyDown={handleKeyDown}
          placeholder="Enter ticker e.g. AAPL"
          maxLength={12}
          disabled={isLoading}
          className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-white/10 bg-white/5 backdrop-blur
                     text-white placeholder-white/25 focus:outline-none focus:ring-2 focus:ring-violet-500/50
                     focus:border-violet-500/50 disabled:opacity-50 text-base font-medium transition-all duration-200"
          aria-label="Stock or crypto ticker symbol"
        />
      </div>
      <button
        id="analyze-button"
        onClick={onSubmit}
        disabled={isLoading || !value.trim()}
        className="px-6 py-3.5 rounded-xl font-semibold text-base transition-all duration-200
                   bg-violet-600 hover:bg-violet-500 active:scale-95
                   text-white shadow-lg shadow-violet-900/30
                   disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100
                   relative overflow-hidden"
        aria-label="Analyze ticker"
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
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
