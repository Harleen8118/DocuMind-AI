import { useState, useCallback, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import client from '../api/client';
import { useAuthStore } from '../store/authStore';

export function useChatSessions(documentId) {
  return useQuery({
    queryKey: ['chatSessions', documentId],
    queryFn: async () => {
      const params = documentId ? { document_id: documentId } : {};
      const { data } = await client.get('/chat/sessions', { params });
      return data;
    },
    enabled: !!documentId,
  });
}

export function useCreateChatSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentId, title }) => {
      const { data } = await client.post('/chat/sessions', {
        document_id: documentId,
        title: title || 'New Chat',
      });
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions', variables.documentId] });
    },
  });
}

export function useChatMessages(sessionId) {
  return useQuery({
    queryKey: ['chatMessages', sessionId],
    queryFn: async () => {
      const { data } = await client.get(`/chat/sessions/${sessionId}/messages`);
      return data;
    },
    enabled: !!sessionId,
  });
}

export function useStreamingChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedContent, setStreamedContent] = useState('');
  const [timestamps, setTimestamps] = useState([]);
  const abortControllerRef = useRef(null);
  const queryClient = useQueryClient();

  const sendMessage = useCallback(async (sessionId, content) => {
    setIsStreaming(true);
    setStreamedContent('');
    setTimestamps([]);

    const token = useAuthStore.getState().token;
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);

            if (data === '[DONE]') {
              continue;
            }

            if (data.startsWith('[TIMESTAMPS]')) {
              try {
                const tsData = JSON.parse(data.slice(12));
                setTimestamps(tsData);
              } catch (e) {
                // Ignore parse errors
              }
              continue;
            }

            if (data.startsWith('[ERROR]')) {
              fullContent += `\n\nError: ${data.slice(7)}`;
              setStreamedContent(fullContent);
              continue;
            }

            fullContent += data;
            setStreamedContent(fullContent);
          }
        }
      }

      // Refresh messages
      queryClient.invalidateQueries({ queryKey: ['chatMessages', sessionId] });
    } catch (error) {
      if (error.name !== 'AbortError') {
        setStreamedContent((prev) => prev + `\n\nError: ${error.message}`);
      }
    } finally {
      setIsStreaming(false);
    }
  }, [queryClient]);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return { sendMessage, cancelStream, isStreaming, streamedContent, timestamps };
}
