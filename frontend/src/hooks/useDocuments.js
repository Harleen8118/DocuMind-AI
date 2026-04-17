import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import client from '../api/client';

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const { data } = await client.get('/documents/');
      return data;
    },
  });
}

export function useDocument(documentId) {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: async () => {
      const { data } = await client.get(`/documents/${documentId}`);
      return data;
    },
    enabled: !!documentId,
    refetchInterval: (query) => {
      const doc = query.state.data;
      if (doc && (doc.status === 'pending' || doc.status === 'processing')) {
        return 3000; // Poll every 3s while processing
      }
      return false;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file) => {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await client.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId) => {
      await client.delete(`/documents/${documentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
}

export function useSummarizeDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId) => {
      const { data } = await client.post(`/documents/${documentId}/summarize`);
      return data;
    },
    onSuccess: (_, documentId) => {
      queryClient.invalidateQueries({ queryKey: ['document', documentId] });
    },
  });
}

export function useDocumentHighlights(documentId) {
  return useQuery({
    queryKey: ['highlights', documentId],
    queryFn: async () => {
      const { data } = await client.get(`/documents/${documentId}/highlights`);
      return data;
    },
    enabled: !!documentId,
  });
}
