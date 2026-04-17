import { FileText, Music, Video, Trash2, BookOpen, Loader2, Clock } from 'lucide-react';
import { useDeleteDocument } from '../hooks/useDocuments';

const FILE_TYPE_CONFIG = {
  pdf: { icon: FileText, color: 'text-red-400', bgColor: 'bg-red-500/10', label: 'PDF' },
  audio: { icon: Music, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'Audio' },
  video: { icon: Video, color: 'text-blue-400', bgColor: 'bg-blue-500/10', label: 'Video' },
};

const STATUS_CONFIG = {
  pending: { class: 'status-pending', label: 'Pending' },
  processing: { class: 'status-processing', label: 'Processing' },
  ready: { class: 'status-ready', label: 'Ready' },
  error: { class: 'status-error', label: 'Error' },
};

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return date.toLocaleDateString();
}

export default function DocumentList({ documents, isLoading, selectedId, onSelect, onShowSummary }) {
  const deleteDoc = useDeleteDocument();

  if (isLoading) {
    return (
      <div className="p-4 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="shimmer-loading h-20 rounded-xl" />
        ))}
      </div>
    );
  }

  if (!documents.length) {
    return (
      <div className="p-6 text-center">
        <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-surface-800/50 flex items-center justify-center">
          <FileText className="w-6 h-6 text-surface-600" />
        </div>
        <p className="text-surface-400 text-sm">No documents yet</p>
        <p className="text-surface-500 text-xs mt-1">Upload your first file to begin</p>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-1">
      {documents.map((doc) => {
        const typeConfig = FILE_TYPE_CONFIG[doc.file_type] || FILE_TYPE_CONFIG.pdf;
        const statusConfig = STATUS_CONFIG[doc.status] || STATUS_CONFIG.pending;
        const Icon = typeConfig.icon;
        const isSelected = selectedId === doc.id;

        return (
          <div
            key={doc.id}
            id={`doc-${doc.id}`}
            onClick={() => onSelect(doc.id)}
            className={`
              group p-3 rounded-xl cursor-pointer transition-all duration-200
              ${isSelected
                ? 'bg-brand-600/15 border border-brand-500/30'
                : 'hover:bg-surface-800/50 border border-transparent'
              }
            `}
          >
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-lg ${typeConfig.bgColor} flex items-center justify-center flex-shrink-0`}>
                <Icon className={`w-5 h-5 ${typeConfig.color}`} />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{doc.original_filename}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={statusConfig.class}>{statusConfig.label}</span>
                  <span className="text-xs text-surface-500">{formatSize(doc.file_size)}</span>
                </div>
                <div className="flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3 text-surface-600" />
                  <span className="text-xs text-surface-500">{formatDate(doc.created_at)}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {doc.status === 'ready' && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onShowSummary(doc.id); }}
                    className="p-1.5 rounded-lg hover:bg-surface-700/50 text-surface-400 hover:text-brand-400 transition-colors"
                    title="Summarize"
                  >
                    <BookOpen className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete this document?')) {
                      deleteDoc.mutate(doc.id);
                    }
                  }}
                  className="p-1.5 rounded-lg hover:bg-red-500/10 text-surface-400 hover:text-red-400 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
