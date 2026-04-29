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
    <div className="flex gap-3 w-full max-w-lg mx-auto">
      <input
        id="ticker-input"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value.toUpperCase())}
        onKeyDown={handleKeyDown}
        placeholder="Enter ticker e.g. AAPL"
        maxLength={12}
        disabled={isLoading}
        className="flex-1 px-4 py-3 rounded-xl border border-white/20 bg-white/10 backdrop-blur
                   text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-violet-400
                   disabled:opacity-50 text-lg font-medium"
        aria-label="Stock or crypto ticker symbol"
      />
      <button
        id="analyze-button"
        onClick={onSubmit}
        disabled={isLoading || !value.trim()}
        className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 active:bg-violet-700
                   text-white font-semibold text-lg transition-all duration-200
                   disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
        aria-label="Analyze ticker"
      >
        {isLoading ? "Analyzing…" : "Analyze"}
      </button>
    </div>
  );
}
