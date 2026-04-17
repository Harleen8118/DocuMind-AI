import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Loader2, Plus, MessageSquare, Bot, User, StopCircle } from 'lucide-react';
import { useChatSessions, useCreateChatSession, useChatMessages, useStreamingChat } from '../hooks/useChat';
import TimestampList from './TimestampList';

export default function ChatWindow({ documentId, document, sessionId, onSessionChange, onTimestampClick }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const { data: sessionsData } = useChatSessions(documentId);
  const createSession = useCreateChatSession();
  const { data: messages = [] } = useChatMessages(sessionId);
  const { sendMessage, cancelStream, isStreaming, streamedContent, timestamps } = useStreamingChat();

  // Auto-select or create session
  useEffect(() => {
    if (documentId && sessionsData?.sessions?.length > 0 && !sessionId) {
      onSessionChange(sessionsData.sessions[0].id);
    }
  }, [documentId, sessionsData, sessionId, onSessionChange]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamedContent]);

  const handleCreateSession = useCallback(async () => {
    const result = await createSession.mutateAsync({
      documentId,
      title: document?.original_filename ? `Chat: ${document.original_filename}` : 'New Chat',
    });
    onSessionChange(result.id);
  }, [createSession, documentId, document, onSessionChange]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isStreaming || !sessionId) return;

    const message = input.trim();
    setInput('');
    await sendMessage(sessionId, message);
  }, [input, isStreaming, sessionId, sendMessage]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const isReady = document?.status === 'ready';

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="px-6 py-3 border-b border-surface-800 flex items-center justify-between bg-surface-950/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <MessageSquare className="w-5 h-5 text-brand-400" />
          <div>
            <h3 className="text-sm font-semibold text-white">
              {document?.original_filename || 'Chat'}
            </h3>
            <p className="text-xs text-surface-500">
              {isReady ? 'Ready to chat' : document?.status === 'processing' ? 'Processing...' : 'Select a document'}
            </p>
          </div>
        </div>

        {documentId && isReady && (
          <button
            id="new-chat-button"
            onClick={handleCreateSession}
            className="btn-ghost text-xs flex items-center gap-1.5"
            disabled={createSession.isPending}
          >
            <Plus className="w-3.5 h-3.5" />
            New Chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {!sessionId && isReady && (
          <div className="text-center py-8 animate-fade-in">
            <Bot className="w-12 h-12 mx-auto mb-3 text-brand-400" />
            <p className="text-surface-300 font-medium">Start a conversation</p>
            <p className="text-surface-500 text-sm mt-1 mb-4">Ask anything about your document</p>
            <button onClick={handleCreateSession} className="btn-primary text-sm">
              <Plus className="w-4 h-4 inline mr-1" /> Start Chat
            </button>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 animate-slide-up ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0 shadow-md">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}

            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-brand-600/20 border border-brand-500/20 text-white'
                  : 'glass-panel-light text-surface-200'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.timestamps_json && (
                <TimestampList
                  timestampsJson={msg.timestamps_json}
                  onTimestampClick={onTimestampClick}
                />
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-surface-700 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-surface-300" />
              </div>
            )}
          </div>
        ))}

        {/* Streaming response */}
        {isStreaming && streamedContent && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0 shadow-md animate-pulse-soft">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="max-w-[75%] glass-panel-light rounded-2xl px-4 py-3">
              <p className="text-sm whitespace-pre-wrap text-surface-200 leading-relaxed">
                {streamedContent}
                <span className="inline-block w-1.5 h-4 bg-brand-400 ml-0.5 animate-pulse rounded-sm" />
              </p>
            </div>
          </div>
        )}

        {isStreaming && !streamedContent && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0 shadow-md">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="glass-panel-light rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce [animation-delay:0ms]" />
                  <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce [animation-delay:150ms]" />
                  <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce [animation-delay:300ms]" />
                </div>
                <span className="text-xs text-surface-500">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      {sessionId && isReady && (
        <div className="px-6 py-4 border-t border-surface-800 bg-surface-950/50 backdrop-blur-sm">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                id="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your document..."
                className="input-field resize-none min-h-[48px] max-h-32 pr-4"
                rows={1}
                disabled={isStreaming}
              />
            </div>

            {isStreaming ? (
              <button
                onClick={cancelStream}
                className="btn-danger p-3 rounded-xl flex-shrink-0"
                title="Stop generating"
              >
                <StopCircle className="w-5 h-5" />
              </button>
            ) : (
              <button
                id="send-message-button"
                onClick={handleSend}
                disabled={!input.trim()}
                className="btn-primary p-3 rounded-xl flex-shrink-0"
                title="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
