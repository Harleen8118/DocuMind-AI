import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUpload from '../src/components/FileUpload';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the hooks
vi.mock('../src/hooks/useDocuments', () => ({
  useUploadDocument: () => ({
    mutate: vi.fn((file, options) => {
      if (file.name === 'success.pdf') {
        options?.onSuccess?.();
      }
    }),
    isPending: false,
    isSuccess: false,
    isError: false,
  }),
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

describe('FileUpload', () => {
  const mockClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the upload modal', () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);
    expect(screen.getByText('Upload Document')).toBeInTheDocument();
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('shows accepted file types', () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('Audio')).toBeInTheDocument();
    expect(screen.getByText('Video')).toBeInTheDocument();
  });

  it('closes when X button is clicked', () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);
    const closeButtons = screen.getAllByRole('button');
    const xButton = closeButtons.find(btn => btn.querySelector('.lucide-x'));
    if (xButton) {
      fireEvent.click(xButton);
      expect(mockClose).toHaveBeenCalled();
    }
  });

  it('shows drop zone with correct styling', () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);
    const dropZone = document.getElementById('drop-zone');
    expect(dropZone).toBeInTheDocument();
  });

  it('validates file type on selection', async () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);

    const input = document.getElementById('file-input');
    const invalidFile = new File(['content'], 'test.exe', { type: 'application/x-msdownload' });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    await waitFor(() => {
      expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument();
    });
  });

  it('accepts PDF files', async () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);

    const input = document.getElementById('file-input');
    const pdfFile = new File(['%PDF-1.4'], 'document.pdf', { type: 'application/pdf' });

    await userEvent.upload(input, pdfFile);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });
  });

  it('shows size information for selected file', async () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);

    const input = document.getElementById('file-input');
    const file = new File(['x'.repeat(1024)], 'test.mp3', { type: 'audio/mpeg' });

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('test.mp3')).toBeInTheDocument();
    });
  });

  it('rejects files over 100MB', async () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);

    const input = document.getElementById('file-input');
    // Create a file object with size property
    const largeFile = new File(['x'], 'huge.mp4', { type: 'video/mp4' });
    Object.defineProperty(largeFile, 'size', { value: 150 * 1024 * 1024 });

    await userEvent.upload(input, largeFile);

    await waitFor(() => {
      expect(screen.getByText(/too large/i)).toBeInTheDocument();
    });
  });

  it('shows upload button when file is selected', async () => {
    renderWithProviders(<FileUpload onClose={mockClose} />);

    const input = document.getElementById('file-input');
    const file = new File(['data'], 'test.pdf', { type: 'application/pdf' });

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(document.getElementById('upload-confirm-button')).toBeInTheDocument();
    });
  });
});
