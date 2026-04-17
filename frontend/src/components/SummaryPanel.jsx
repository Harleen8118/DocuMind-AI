import { useState } from 'react';
import { useSummarizeDocument } from '../hooks/useDocuments';
import { useDocument } from '../hooks/useDocuments';
import { X, BookOpen, Copy, Check, Loader2 } from 'lucide-react';

export default function SummaryPanel({ documentId, onClose }) {
  const { data: document } = useDocument(documentId);
  const summarize = useSummarizeDocument();
  const [copied, setCopied] = useState(false);

  const summary = document?.summary_text || summarize.data?.summary;

  const handleSummarize = () => {
    summarize.mutate(documentId);
  };

  const handleCopy = () => {
    if (summary) {
      navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-surface-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-brand-400" />
          <h3 className="text-sm font-semibold text-white">Document Summary</h3>
        </div>
        <div className="flex items-center gap-2">
          {summary && (
            <button onClick={handleCopy} className="btn-ghost p-1.5 rounded-lg" title="Copy summary">
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
          )}
          <button onClick={onClose} className="btn-ghost p-1.5 rounded-lg">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {summary ? (
          <div className="prose prose-invert prose-sm max-w-none">
            <div className="text-sm text-surface-300 leading-relaxed whitespace-pre-wrap">
              {summary}
            </div>
          </div>
        ) : summarize.isPending ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-brand-400 animate-spin mb-3" />
            <p className="text-surface-400 text-sm">Generating summary...</p>
            <p className="text-surface-500 text-xs mt-1">This may take a moment</p>
          </div>
        ) : summarize.isError ? (
          <div className="text-center py-12">
            <p className="text-red-400 text-sm mb-3">
              {summarize.error?.response?.data?.detail || 'Failed to generate summary'}
            </p>
            <button onClick={handleSummarize} className="btn-secondary text-sm">
              Try Again
            </button>
          </div>
        ) : (
          <div className="text-center py-12">
            <BookOpen className="w-10 h-10 mx-auto mb-3 text-surface-600" />
            <p className="text-surface-400 text-sm mb-4">
              Generate an AI-powered summary of this document
            </p>
            <button
              id="generate-summary-button"
              onClick={handleSummarize}
              className="btn-primary text-sm"
            >
              Generate Summary
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
