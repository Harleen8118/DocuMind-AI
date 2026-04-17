import { useState, useCallback } from 'react';
import Layout from '../components/Layout';
import FileUpload from '../components/FileUpload';
import DocumentList from '../components/DocumentList';
import ChatWindow from '../components/ChatWindow';
import MediaPlayer from '../components/MediaPlayer';
import HighlightReel from '../components/HighlightReel';
import SummaryPanel from '../components/SummaryPanel';
import { useDocuments, useDocument } from '../hooks/useDocuments';

export default function Dashboard() {
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const { data: documentsData, isLoading: docsLoading } = useDocuments();
  const { data: selectedDoc } = useDocument(selectedDocId);

  const isMediaFile = selectedDoc && (selectedDoc.file_type === 'audio' || selectedDoc.file_type === 'video');

  const handleSelectDocument = useCallback((docId) => {
    setSelectedDocId(docId);
    setSelectedSessionId(null);
    setShowSummary(false);
  }, []);

  const handleTimestampClick = useCallback((timeSeconds) => {
    setCurrentTime(timeSeconds);
  }, []);

  return (
    <Layout>
      <div className="flex h-[calc(100vh-64px)] overflow-hidden">
        {/* Left Sidebar: Documents */}
        <div className="w-80 flex-shrink-0 border-r border-surface-800 flex flex-col bg-surface-950/50">
          <div className="p-4 border-b border-surface-800">
            <button
              id="upload-button"
              onClick={() => setShowUpload(true)}
              className="btn-primary w-full text-sm"
            >
              Upload Document
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            <DocumentList
              documents={documentsData?.documents || []}
              isLoading={docsLoading}
              selectedId={selectedDocId}
              onSelect={handleSelectDocument}
              onShowSummary={(id) => { setSelectedDocId(id); setShowSummary(true); }}
            />
          </div>
        </div>

        {/* Center: Chat */}
        <div className="flex-1 flex flex-col min-w-0">
          {selectedDocId ? (
            <ChatWindow
              documentId={selectedDocId}
              document={selectedDoc}
              sessionId={selectedSessionId}
              onSessionChange={setSelectedSessionId}
              onTimestampClick={handleTimestampClick}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center animate-fade-in">
                <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-surface-800/50 flex items-center justify-center">
                  <svg className="w-10 h-10 text-surface-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-surface-300 mb-2">Select a document</h2>
                <p className="text-surface-500 text-sm max-w-sm">
                  Upload or select a document from the sidebar to start chatting with AI about its content.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar: Media Player + Highlights */}
        {selectedDocId && isMediaFile && (
          <div className="w-96 flex-shrink-0 border-l border-surface-800 flex flex-col bg-surface-950/50 overflow-y-auto">
            <MediaPlayer
              document={selectedDoc}
              seekTo={currentTime}
            />
            <HighlightReel
              documentId={selectedDocId}
              onTimestampClick={handleTimestampClick}
            />
          </div>
        )}

        {/* Right Sidebar: Summary for PDFs */}
        {selectedDocId && showSummary && !isMediaFile && (
          <div className="w-96 flex-shrink-0 border-l border-surface-800 bg-surface-950/50 overflow-y-auto">
            <SummaryPanel
              documentId={selectedDocId}
              onClose={() => setShowSummary(false)}
            />
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <FileUpload onClose={() => setShowUpload(false)} />
      )}
    </Layout>
  );
}
