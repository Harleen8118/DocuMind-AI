import { useMemo } from 'react';
import { Clock } from 'lucide-react';

export default function TimestampList({ timestampsJson, onTimestampClick }) {
  const timestamps = useMemo(() => {
    if (!timestampsJson) return [];
    try {
      const parsed = JSON.parse(timestampsJson);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, [timestampsJson]);

  if (!timestamps.length) return null;

  return (
    <div className="mt-3 pt-3 border-t border-surface-700/30">
      <div className="flex flex-wrap gap-1.5">
        {timestamps.map((ts, index) => (
          <button
            key={index}
            onClick={(e) => {
              e.stopPropagation();
              onTimestampClick?.(ts.time_seconds);
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-brand-600/15 hover:bg-brand-600/25 border border-brand-500/20 hover:border-brand-500/40 transition-all text-xs group"
            title={ts.label}
          >
            <Clock className="w-3 h-3 text-brand-400" />
            <span className="font-mono text-brand-300">{ts.time_formatted}</span>
            {ts.label && (
              <span className="text-surface-400 max-w-[120px] truncate group-hover:text-surface-300">
                {ts.label}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
