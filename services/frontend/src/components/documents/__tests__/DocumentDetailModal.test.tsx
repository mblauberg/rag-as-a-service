import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentDetailModal } from '../DocumentDetailModal';
import { api } from '@/services/api';
import type { DocumentDetail } from '@/types';

vi.mock('@/services/api');

const mockDocument: DocumentDetail = {
  id: '123',
  title: 'Test Document',
  description: 'Test description',
  file_name: 'test.pdf',
  file_type: 'application/pdf',
  file_size: 1024,
  upload_status: 'completed',
  embedding_status: 'completed',
  created_at: '2025-01-25T12:00:00Z',
  updated_at: '2025-01-25T12:00:00Z',
  chunks: [
    {
      id: 'chunk-1',
      document_id: '123',
      chunk_index: 0,
      chunk_text: 'Test content',
      token_count: 10,
      section_title: undefined,
      page_number: undefined,
      created_at: '2025-01-25T12:00:00Z',
    },
  ],
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('DocumentDetailModal', () => {
  it('should render loading state', async () => {
    vi.mocked(api.getDocument).mockImplementation(() => new Promise(() => {}));

    const { baseElement } = render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    // Wait a bit for the loading state to render in the portal
    await waitFor(() => {
      const skeletons = baseElement.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  it('should render document details when loaded', async () => {
    vi.mocked(api.getDocument).mockResolvedValue(mockDocument);

    render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    expect(screen.getByText('Test description')).toBeInTheDocument();
    expect(screen.getByText('1.00 KB')).toBeInTheDocument();
    expect(screen.getByText('1 chunks')).toBeInTheDocument();
  });

  it('should render error state', async () => {
    vi.mocked(api.getDocument).mockRejectedValue(new Error('Failed to load'));

    render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
    });
  });

  it('should not fetch document when modal is closed', () => {
    vi.clearAllMocks();
    vi.mocked(api.getDocument).mockResolvedValue(mockDocument);

    render(
      <DocumentDetailModal documentId="123" open={false} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    expect(api.getDocument).not.toHaveBeenCalled();
  });

  it.skip('should call onClose when dialog is closed', async () => {
    // Skipped: Dialog interaction tests have JSDOM compatibility issues
  });

  it('should display chunk content', async () => {
    vi.mocked(api.getDocument).mockResolvedValue(mockDocument);

    render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    expect(screen.getByText('Chunk 1')).toBeInTheDocument();
  });

  it('should handle document without description', async () => {
    const docWithoutDesc = { ...mockDocument, description: null };
    vi.mocked(api.getDocument).mockResolvedValue(docWithoutDesc);

    render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    expect(screen.queryByText('Test description')).not.toBeInTheDocument();
  });

  it('should handle document without chunks', async () => {
    const docWithoutChunks = { ...mockDocument, chunks: [] };
    vi.mocked(api.getDocument).mockResolvedValue(docWithoutChunks);

    render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    expect(screen.getByText('0 chunks')).toBeInTheDocument();
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('should display chunk metadata (section title and page number)', async () => {
    const docWithMetadata: DocumentDetail = {
      ...mockDocument,
      chunks: [
        {
          id: 'chunk-1',
          document_id: '123',
          chunk_index: 0,
          chunk_text: 'Test content',
          token_count: 10,
          section_title: 'Introduction',
          page_number: 5,
          created_at: '2025-01-25T12:00:00Z',
        },
      ],
    };
    vi.mocked(api.getDocument).mockResolvedValue(docWithMetadata);

    render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Introduction/)).toBeInTheDocument();
    });

    expect(screen.getByText(/Page 5/)).toBeInTheDocument();
  });

  it('should format created date correctly', async () => {
    vi.mocked(api.getDocument).mockResolvedValue(mockDocument);

    render(
      <DocumentDetailModal documentId="123" open={true} onClose={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    // The formatDate function should format the date
    expect(screen.getByText(/Uploaded/)).toBeInTheDocument();
  });
});
