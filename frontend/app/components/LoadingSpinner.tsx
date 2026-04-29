/**
 * components/LoadingSpinner.tsx — Reusable loading indicator (FR-014).
 */

interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center gap-3 py-8 text-white/60">
      <div
        className="w-10 h-10 border-4 border-white/20 border-t-violet-400 rounded-full animate-spin"
        role="status"
        aria-label="Loading"
      />
      {message && <p className="text-sm font-medium">{message}</p>}
    </div>
  );
}
