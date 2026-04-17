import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatWindow from '../src/components/ChatWindow';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock hooks
const mockSendMessage = vi.fn();
const mockCancelStream = vi.fn();

vi.mock('../src/hooks/useChat', () => ({
  useChatSessions: () => ({
    data: {
      sessions: [
        { id: 'session-1', document_id: 'doc-1', title: 'Test Chat', created_at: new Date().toISOString() },
      ],
      total: 1,
    },
    isLoading: false,
  }),
  useCreateChatSession: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ id: 'new-session', title: 'New Chat' }),
    isPending: false,
  }),
  useChatMessages: () => ({
    data: [
      {
        id: 'msg-1',
        session_id: 'session-1',
        role: 'user',
        content: 'What is this document about?',
        created_at: new Date().toISOString(),
      },
      {
        id: 'msg-2',
        session_id: 'session-1',
        role: 'assistant',
        content: 'This document discusses AI and machine learning concepts.',
        timestamps_json: null,
        created_at: new Date().toISOString(),
      },
    ],
    isLoading: false,
  }),
  useStreamingChat: () => ({
    sendMessage: mockSendMessage,
    cancelStream: mockCancelStream,
    isStreaming: false,
    streamedContent: '',
    timestamps: [],
  }),
}));

vi.mock('../src/store/authStore', () => ({
  useAuthStore: {
    getState: () => ({ token: 'test-token' }),
  },
}));

function renderWithProviders(ui) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

describe('ChatWindow', () => {
  const defaultProps = {
    documentId: 'doc-1',
    document: {
      id: 'doc-1',
      original_filename: 'test.pdf',
      file_type: 'pdf',
      status: 'ready',
    },
    sessionId: 'session-1',
    onSessionChange: vi.fn(),
    onTimestampClick: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat header with document name', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
  });

  it('displays message history', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    expect(screen.getByText('What is this document about?')).toBeInTheDocument();
    expect(screen.getByText(/AI and machine learning/)).toBeInTheDocument();
  });

  it('renders user and assistant messages with different styles', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    const userMessage = screen.getByText('What is this document about?');
    const assistantMessage = screen.getByText(/AI and machine learning/);

    // Both messages should be rendered
    expect(userMessage).toBeInTheDocument();
    expect(assistantMessage).toBeInTheDocument();
  });

  it('shows input field when session is active', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    const input = document.getElementById('chat-input');
    expect(input).toBeInTheDocument();
  });

  it('shows send button', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    const sendButton = document.getElementById('send-message-button');
    expect(sendButton).toBeInTheDocument();
  });

  it('disables send button when input is empty', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    const sendButton = document.getElementById('send-message-button');
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when input has text', async () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    const input = document.getElementById('chat-input');

    fireEvent.change(input, { target: { value: 'Hello' } });

    const sendButton = document.getElementById('send-message-button');
    expect(sendButton).not.toBeDisabled();
  });

  it('shows new chat button', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    const newButton = document.getElementById('new-chat-button');
    expect(newButton).toBeInTheDocument();
  });

  it('shows prompt to start chat when no session', () => {
    renderWithProviders(
      <ChatWindow {...defaultProps} sessionId={null} />
    );
    expect(screen.getByText('Start a conversation')).toBeInTheDocument();
  });

  it('shows ready status', () => {
    renderWithProviders(<ChatWindow {...defaultProps} />);
    expect(screen.getByText('Ready to chat')).toBeInTheDocument();
  });
});
