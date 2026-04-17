import { useDocumentHighlights } from '../hooks/useDocuments';
import { Sparkles, Clock, Play, Loader2, Star } from 'lucide-react';

export default function HighlightReel({ documentId, onTimestampClick }) {
  const { data, isLoading, isError } = useDocumentHighlights(documentId);
  const highlights = data?.highlights || [];

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-surface-300">Smart Highlight Reel</h3>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="shimmer-loading h-20 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !highlights.length) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-surface-300">Smart Highlight Reel</h3>
        </div>
        <div className="text-center py-6">
          <Sparkles className="w-8 h-8 mx-auto mb-2 text-surface-600" />
          <p className="text-sm text-surface-500">
            {isError ? 'Failed to load highlights' : 'No highlights available yet'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-semibold text-surface-300">Smart Highlight Reel</h3>
        <span className="ml-auto text-xs text-surface-500">{highlights.length} moments</span>
      </div>

      <div className="space-y-2">
        {highlights.map((highlight, index) => (
          <button
            key={index}
            id={`highlight-${index}`}
            onClick={() => onTimestampClick(highlight.timestamp)}
            className="w-full text-left group glass-panel-light p-3 card-hover"
          >
            <div className="flex items-start gap-3">
              {/* Play indicator */}
              <div className="w-10 h-10 rounded-lg bg-brand-600/20 flex items-center justify-center flex-shrink-0 group-hover:bg-brand-600/30 transition-colors">
                <Play className="w-4 h-4 text-brand-400 group-hover:scale-110 transition-transform" />
              </div>

              <div className="flex-1 min-w-0">
                {/* Timestamp */}
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded-md">
                    {highlight.timestamp_formatted}
                  </span>
                  {highlight.importance_score >= 0.9 && (
                    <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                  )}
                </div>

                {/* Summary */}
                <p className="text-sm text-surface-300 leading-snug line-clamp-2">
                  {highlight.summary}
                </p>
              </div>
            </div>

            {/* Importance bar */}
            {highlight.importance_score != null && (
              <div className="mt-2 ml-[52px]">
                <div className="h-1 bg-surface-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-brand-500 to-accent-cyan rounded-full transition-all"
                    style={{ width: `${highlight.importance_score * 100}%` }}
                  />
                </div>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
