/**
 * components/LoadingSpinner.tsx — Skeleton loading state (FR-014).
 */

"use client";

interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message }: LoadingSpinnerProps) {
  return (
    <div className="glass p-8 flex flex-col items-center justify-center gap-4 fade-up">
      {/* Animated rings */}
      <div className="relative w-10 h-10">
        <div className="absolute inset-0 rounded-full border-2 border-violet-500/20" />
        <div className="absolute inset-0 rounded-full border-t-2 border-violet-500 animate-spin" />
      </div>
      {message && (
        <p className="text-white/40 text-sm tracking-wide">{message}</p>
      )}
      {/* Skeleton bars */}
      <div className="w-full flex flex-col gap-2 mt-2">
        {[80, 60, 72].map((w, i) => (
          <div
            key={i}
            className="h-2 rounded-full bg-white/5 pulse-ring"
            style={{ width: `${w}%`, animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
