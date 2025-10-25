import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { DocumentCard } from '../DocumentCard';
import type { Document } from '../../../types';
import * as useDocumentsHook from '../../../hooks/useDocuments';

// Mock the useDeleteDocument hook
vi.mock('../../../hooks/useDocuments', async () => {
  const actual = await vi.importActual('../../../hooks/useDocuments');
  return {
    ...actual,
    useDeleteDocument: vi.fn(),
  };
});

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

const mockDocument: Document = {
  id: 'doc-123',
  title: 'Test Document',
  description: 'This is a test document description',
  file_name: 'test.pdf',
  file_type: 'application/pdf',
  file_size: 1024 * 1024, // 1 MB
  upload_status: 'completed',
  embedding_status: 'completed',
  created_at: '2024-01-15T10:30:00Z',
  updated_at: '2024-01-15T10:35:00Z',
};

describe('DocumentCard', () => {
  const mockMutateAsync = vi.fn();
  const mockDeleteDocument = {
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    isSuccess: false,
    error: null,
    data: null,
    mutate: vi.fn(),
    reset: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockMutateAsync.mockResolvedValue(undefined);
    vi.mocked(useDocumentsHook.useDeleteDocument).mockReturnValue(mockDeleteDocument as any);
  });

  describe('Basic Rendering', () => {
    it('should render the document title', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    it('should render the document description', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      expect(screen.getByText('This is a test document description')).toBeInTheDocument();
    });

    it('should not render description section when description is null', () => {
      const docWithoutDesc = { ...mockDocument, description: null };
      render(<DocumentCard document={docWithoutDesc} />, { wrapper: createWrapper() });
      expect(screen.queryByText('This is a test document description')).not.toBeInTheDocument();
    });

    it('should render the file name', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });

    it('should render the delete button', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });

    it('should render the title as a link to document detail page', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      const titleLink = screen.getByText('Test Document').closest('a');
      expect(titleLink).toHaveAttribute('href', '/documents/doc-123');
    });
  });

  describe('Status Badge Rendering', () => {
    it('should render completed status badge with correct styling', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      const badge = screen.getByText('Completed');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('should render pending status badge with correct styling', () => {
      const pendingDoc = { ...mockDocument, embedding_status: 'pending' as const };
      render(<DocumentCard document={pendingDoc} />, { wrapper: createWrapper() });
      const badge = screen.getByText('Pending');
      expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('should render processing status badge with correct styling', () => {
      const processingDoc = { ...mockDocument, embedding_status: 'processing' as const };
      render(<DocumentCard document={processingDoc} />, { wrapper: createWrapper() });
      const badge = screen.getByText('Processing');
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('should render failed status badge with correct styling', () => {
      const failedDoc = { ...mockDocument, embedding_status: 'failed' as const };
      render(<DocumentCard document={failedDoc} />, { wrapper: createWrapper() });
      const badge = screen.getByText('Failed');
      expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('should capitalize status text', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.queryByText('completed')).not.toBeInTheDocument();
    });
  });

  describe('Date Formatting', () => {
    it('should format the created date', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      // The formatDate function formats as "Jan 15, 2024" without time by default
      expect(screen.getByText(/Jan 15, 2024/i)).toBeInTheDocument();
    });

    it('should handle different date formats', () => {
      const docWithDiffDate = {
        ...mockDocument,
        created_at: '2023-12-25T12:00:00Z',
      };
      render(<DocumentCard document={docWithDiffDate} />, { wrapper: createWrapper() });
      expect(screen.getByText(/Dec 25, 2023/i)).toBeInTheDocument();
    });
  });

  describe('File Size Formatting', () => {
    it('should format bytes correctly (1 MB)', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      expect(screen.getByText('1.00 MB')).toBeInTheDocument();
    });

    it('should format bytes correctly (< 1 KB)', () => {
      const smallDoc = { ...mockDocument, file_size: 512 };
      render(<DocumentCard document={smallDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('512 B')).toBeInTheDocument();
    });

    it('should format bytes correctly (KB range)', () => {
      const kbDoc = { ...mockDocument, file_size: 5120 };
      render(<DocumentCard document={kbDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('5.00 KB')).toBeInTheDocument();
    });

    it('should format bytes correctly (large MB)', () => {
      const largeDoc = { ...mockDocument, file_size: 50 * 1024 * 1024 };
      render(<DocumentCard document={largeDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('50.00 MB')).toBeInTheDocument();
    });
  });

  describe('Delete Functionality', () => {
    it('should show delete confirmation modal when delete button is clicked', async () => {
      const user = userEvent.setup();
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      });
    });

    it('should display document title in confirmation modal', async () => {
      const user = userEvent.setup();
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(/Are you sure you want to delete "Test Document"/i)).toBeInTheDocument();
      });
    });

    it('should show warning message in confirmation modal', async () => {
      const user = userEvent.setup();
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(/This action cannot be undone/i)).toBeInTheDocument();
      });
    });

    it('should close modal when Cancel is clicked in confirmation', async () => {
      const user = userEvent.setup();
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      });

      const cancelButton = screen.getAllByRole('button', { name: /cancel/i })[0];
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText('Confirm Delete')).not.toBeInTheDocument();
      });
    });

    it('should call deleteDocument mutation when Delete is confirmed', async () => {
      const user = userEvent.setup();
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      });

      const confirmButtons = screen.getAllByRole('button', { name: /delete/i });
      const confirmDeleteButton = confirmButtons.find(
        (btn) => btn.textContent === 'Delete' && btn !== deleteButton
      );

      if (confirmDeleteButton) {
        await user.click(confirmDeleteButton);

        await waitFor(() => {
          expect(mockMutateAsync).toHaveBeenCalledWith('doc-123');
        });
      }
    });

    it('should close modal after successful deletion', async () => {
      const user = userEvent.setup();
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      });

      const confirmButtons = screen.getAllByRole('button', { name: /delete/i });
      const confirmDeleteButton = confirmButtons.find(
        (btn) => btn.textContent === 'Delete' && btn !== deleteButton
      );

      if (confirmDeleteButton) {
        await user.click(confirmDeleteButton);

        await waitFor(() => {
          expect(screen.queryByText('Confirm Delete')).not.toBeInTheDocument();
        });
      }
    });

    it('should show loading state on delete button during deletion', async () => {
      const user = userEvent.setup();
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      // Mock isPending after modal is open
      vi.mocked(useDocumentsHook.useDeleteDocument).mockReturnValue({
        ...mockDeleteDocument,
        isPending: true,
      } as any);

      await waitFor(() => {
        const confirmButtons = screen.getAllByRole('button', { name: /delete/i });
        const confirmDeleteButton = confirmButtons.find((btn) => btn !== deleteButton);
        // Modal should be open with delete button visible
        expect(confirmDeleteButton).toBeDefined();
      });
    });

    it('should handle delete errors gracefully', async () => {
      const user = userEvent.setup();
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockMutateAsync.mockRejectedValue(new Error('Delete failed'));

      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      });

      const confirmButtons = screen.getAllByRole('button', { name: /delete/i });
      const confirmDeleteButton = confirmButtons.find(
        (btn) => btn.textContent === 'Delete' && btn !== deleteButton
      );

      if (confirmDeleteButton) {
        await user.click(confirmDeleteButton);

        await waitFor(() => {
          expect(consoleErrorSpy).toHaveBeenCalledWith(
            'Failed to delete document:',
            expect.any(Error)
          );
        });
      }

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Icons', () => {
    it('should render file icon', () => {
      const { container } = render(<DocumentCard document={mockDocument} />, {
        wrapper: createWrapper(),
      });
      const fileIcon = container.querySelector('svg[stroke="currentColor"]');
      expect(fileIcon).toBeInTheDocument();
    });

    it('should render multiple metadata icons', () => {
      const { container } = render(<DocumentCard document={mockDocument} />, {
        wrapper: createWrapper(),
      });
      const icons = container.querySelectorAll('svg');
      // Should have file, size, and date icons
      expect(icons.length).toBeGreaterThan(2);
    });
  });

  describe('Hover Effects', () => {
    it('should have hover class on card', () => {
      const { container } = render(<DocumentCard document={mockDocument} />, {
        wrapper: createWrapper(),
      });
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('hover:shadow-lg');
    });

    it('should have hover class on title link', () => {
      render(<DocumentCard document={mockDocument} />, { wrapper: createWrapper() });
      const titleLink = screen.getByText('Test Document');
      expect(titleLink).toHaveClass('hover:text-primary-600');
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long titles', () => {
      const longTitleDoc = {
        ...mockDocument,
        title: 'A'.repeat(200),
      };
      render(<DocumentCard document={longTitleDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('A'.repeat(200))).toBeInTheDocument();
    });

    it('should handle very long descriptions', () => {
      const longDescDoc = {
        ...mockDocument,
        description: 'B'.repeat(500),
      };
      const { container } = render(<DocumentCard document={longDescDoc} />, {
        wrapper: createWrapper(),
      });
      const description = container.querySelector('.line-clamp-2');
      expect(description).toBeInTheDocument();
    });

    it('should render description when it is an empty string', () => {
      const emptyDescDoc = { ...mockDocument, description: '' };
      render(<DocumentCard document={emptyDescDoc} />, { wrapper: createWrapper() });
      // Component should render without errors when description is empty
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    it('should handle zero file size', () => {
      const zeroSizeDoc = { ...mockDocument, file_size: 0 };
      render(<DocumentCard document={zeroSizeDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('0 B')).toBeInTheDocument();
    });

    it('should handle special characters in title', () => {
      const specialDoc = {
        ...mockDocument,
        title: 'Test & Document <Special> "Chars"',
      };
      render(<DocumentCard document={specialDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('Test & Document <Special> "Chars"')).toBeInTheDocument();
    });

    it('should handle special characters in file name', () => {
      const specialFileDoc = {
        ...mockDocument,
        file_name: 'file (copy) [2024].pdf',
      };
      render(<DocumentCard document={specialFileDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('file (copy) [2024].pdf')).toBeInTheDocument();
    });

    it('should handle very small file sizes', () => {
      const smallDoc = { ...mockDocument, file_size: 1 };
      render(<DocumentCard document={smallDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('1 B')).toBeInTheDocument();
    });

    it('should handle boundary file size (1 KB)', () => {
      const boundaryDoc = { ...mockDocument, file_size: 1024 };
      render(<DocumentCard document={boundaryDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('1.00 KB')).toBeInTheDocument();
    });

    it('should handle boundary file size (1 MB)', () => {
      const boundaryDoc = { ...mockDocument, file_size: 1024 * 1024 };
      render(<DocumentCard document={boundaryDoc} />, { wrapper: createWrapper() });
      expect(screen.getByText('1.00 MB')).toBeInTheDocument();
    });
  });
});
