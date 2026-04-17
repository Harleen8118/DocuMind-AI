import { useState, useCallback } from 'react';
import { useUploadDocument } from '../hooks/useDocuments';
import { Upload, X, FileText, Music, Video, AlertCircle, CheckCircle } from 'lucide-react';

const ACCEPTED_TYPES = {
  'application/pdf': { icon: FileText, label: 'PDF', color: 'text-red-400' },
  'audio/mpeg': { icon: Music, label: 'MP3', color: 'text-emerald-400' },
  'audio/wav': { icon: Music, label: 'WAV', color: 'text-emerald-400' },
  'audio/ogg': { icon: Music, label: 'OGG', color: 'text-emerald-400' },
  'audio/flac': { icon: Music, label: 'FLAC', color: 'text-emerald-400' },
  'video/mp4': { icon: Video, label: 'MP4', color: 'text-blue-400' },
  'video/webm': { icon: Video, label: 'WebM', color: 'text-blue-400' },
  'video/quicktime': { icon: Video, label: 'MOV', color: 'text-blue-400' },
};

export default function FileUpload({ onClose }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');

  const upload = useUploadDocument();

  const validateFile = useCallback((file) => {
    setError('');

    // Check type
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    const validExtensions = ['.pdf', '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.mp4', '.webm', '.mov', '.avi', '.mkv'];
    if (!validExtensions.includes(ext) && !ACCEPTED_TYPES[file.type]) {
      setError('Unsupported file type. Please upload PDF, audio, or video files.');
      return false;
    }

    // Check size (100MB max)
    if (file.size > 100 * 1024 * 1024) {
      setError('File is too large. Maximum size is 100MB.');
      return false;
    }

    return true;
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  }, [validateFile]);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  }, [validateFile]);

  const handleUpload = useCallback(() => {
    if (!selectedFile) return;
    upload.mutate(selectedFile, {
      onSuccess: () => {
        onClose();
      },
      onError: (err) => {
        setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      },
    });
  }, [selectedFile, upload, onClose]);

  const getFileInfo = (file) => {
    const type = ACCEPTED_TYPES[file.type];
    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    return { type, sizeMB };
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg glass-panel p-6 animate-slide-up" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Upload Document</h2>
          <button onClick={onClose} className="btn-ghost p-2 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drop zone */}
        {!selectedFile && (
          <div
            id="drop-zone"
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`
              border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 cursor-pointer
              ${dragActive
                ? 'border-brand-400 bg-brand-500/10'
                : 'border-surface-700 hover:border-surface-500 bg-surface-800/30'
              }
            `}
            onClick={() => document.getElementById('file-input').click()}
          >
            <input
              id="file-input"
              type="file"
              className="hidden"
              accept=".pdf,.mp3,.wav,.ogg,.flac,.m4a,.mp4,.webm,.mov,.avi,.mkv"
              onChange={handleFileSelect}
            />
            <Upload className={`w-12 h-12 mx-auto mb-4 ${dragActive ? 'text-brand-400' : 'text-surface-500'}`} />
            <p className="text-surface-300 font-medium mb-1">
              {dragActive ? 'Drop your file here' : 'Drag & drop your file here'}
            </p>
            <p className="text-surface-500 text-sm">or click to browse</p>
            <div className="mt-4 flex items-center justify-center gap-3 text-xs text-surface-500">
              <span className="flex items-center gap-1"><FileText className="w-3.5 h-3.5 text-red-400" /> PDF</span>
              <span className="flex items-center gap-1"><Music className="w-3.5 h-3.5 text-emerald-400" /> Audio</span>
              <span className="flex items-center gap-1"><Video className="w-3.5 h-3.5 text-blue-400" /> Video</span>
              <span>Max 100MB</span>
            </div>
          </div>
        )}

        {/* Selected file preview */}
        {selectedFile && !upload.isSuccess && (
          <div className="glass-panel-light p-4 flex items-center gap-4">
            {(() => {
              const { type, sizeMB } = getFileInfo(selectedFile);
              const Icon = type?.icon || FileText;
              const color = type?.color || 'text-surface-400';
              return (
                <>
                  <div className={`w-12 h-12 rounded-xl bg-surface-800 flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-6 h-6 ${color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{selectedFile.name}</p>
                    <p className="text-xs text-surface-400">{sizeMB} MB • {type?.label || 'File'}</p>
                  </div>
                  <button
                    onClick={() => { setSelectedFile(null); setError(''); }}
                    className="btn-ghost p-1.5 rounded-lg"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </>
              );
            })()}
          </div>
        )}

        {/* Upload success */}
        {upload.isSuccess && (
          <div className="text-center py-6">
            <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <p className="text-white font-medium">Upload successful!</p>
            <p className="text-surface-400 text-sm mt-1">Your document is being processed...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Actions */}
        {selectedFile && !upload.isSuccess && (
          <div className="mt-6 flex items-center justify-end gap-3">
            <button onClick={onClose} className="btn-secondary text-sm">
              Cancel
            </button>
            <button
              id="upload-confirm-button"
              onClick={handleUpload}
              disabled={upload.isPending}
              className="btn-primary text-sm flex items-center gap-2"
            >
              {upload.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
