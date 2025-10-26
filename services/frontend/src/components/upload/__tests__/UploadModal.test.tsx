import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UploadModal } from '../UploadModal';
import * as useDocumentsHook from '@/hooks/useDocuments';

// Mock the useUploadDocument hook
vi.mock('@/hooks/useDocuments', async () => {
  const actual = await vi.importActual('@/hooks/useDocuments');
  return {
    ...actual,
    useUploadDocument: vi.fn(),
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
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('UploadModal', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  const mockMutateAsync = vi.fn();
  const mockUploadDocument = {
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
    mockMutateAsync.mockResolvedValue({ id: 'doc-123', title: 'Test Doc' });
    vi.mocked(useDocumentsHook.useUploadDocument).mockReturnValue(mockUploadDocument as any);
  });

  describe('Basic Rendering', () => {
    it('should render the upload modal when open', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });
      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });

    it('should not render when closed', () => {
      render(<UploadModal {...defaultProps} open={false} />, { wrapper: createWrapper() });
      expect(screen.queryByText('Upload Document')).not.toBeInTheDocument();
    });

    it('should display the description text', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });
      expect(screen.getByText(/Upload PDF, DOCX, or TXT files up to 100MB/i)).toBeInTheDocument();
    });

    it('should render file input with correct accept attribute', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(fileInput).toBeInTheDocument();
      expect(fileInput.accept).toBe('.pdf,.docx,.txt,.md,.markdown,.csv');
    });

    it('should render title input field', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });
      expect(screen.getByPlaceholderText('Enter document title')).toBeInTheDocument();
    });

    it('should render description textarea', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });
      expect(screen.getByPlaceholderText('Enter document description')).toBeInTheDocument();
    });

    it('should render Cancel and Upload buttons', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
    });
  });

  describe('File Selection via Input', () => {
    it('should handle file selection through input', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/Selected: test.pdf/i)).toBeInTheDocument();
      });
    });

    it('should auto-fill title from filename', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'my-document.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        const titleInput = screen.getByPlaceholderText('Enter document title') as HTMLInputElement;
        expect(titleInput.value).toBe('my-document');
      });
    });

    it('should not overwrite existing title when selecting file', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const titleInput = screen.getByPlaceholderText('Enter document title');
      await userEvent.type(titleInput, 'Custom Title');

      const file = new File(['test'], 'file.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        const updatedInput = screen.getByPlaceholderText('Enter document title') as HTMLInputElement;
        expect(updatedInput.value).toBe('Custom Title');
      });
    });
  });

  describe('File Validation', () => {
    it('should show error for file size exceeding 100MB', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const largeFile = new File(['test'], 'large.pdf', {
        type: 'application/pdf',
      });
      // Mock the file size to be over 100MB
      Object.defineProperty(largeFile, 'size', {
        value: 101 * 1024 * 1024,
        writable: false,
      });

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [largeFile],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText('File size must be less than 100MB')).toBeInTheDocument();
      });
    });

    it('should accept file with exactly 100MB', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'exact.pdf', {
        type: 'application/pdf',
      });
      // Mock the file size to be exactly 100MB
      Object.defineProperty(file, 'size', {
        value: 100 * 1024 * 1024,
        writable: false,
      });

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.queryByText('File size must be less than 100MB')).not.toBeInTheDocument();
      });
    });

    it('should accept PDF files', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'doc.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/Selected: doc.pdf/i)).toBeInTheDocument();
      });
    });

    it('should accept DOCX files', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'doc.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/Selected: doc.docx/i)).toBeInTheDocument();
      });
    });

    it('should accept TXT files', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'doc.txt', { type: 'text/plain' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/Selected: doc.txt/i)).toBeInTheDocument();
      });
    });
  });

  describe('Drag and Drop', () => {
    it('should render drop zone with correct UI elements', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      // Check for file upload input
      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument();

      // Check for upload label
      expect(screen.getByText(/Click to upload/i)).toBeInTheDocument();
    });

    it('should have drag event handlers on drop zone', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const dropZone = screen.getByText(/Click to upload/i).closest('div')?.parentElement;
      expect(dropZone).toBeInTheDocument();

      // Verify drop zone can handle drag events (handlers are attached)
      if (dropZone) {
        fireEvent.dragOver(dropZone);
        expect(dropZone).toBeInTheDocument(); // Should not crash
      }
    });

    it('should handle dragenter event', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const dropZone = screen.getByText(/Click to upload/i).closest('div')?.parentElement;

      if (dropZone) {
        fireEvent.dragEnter(dropZone, {
          dataTransfer: {
            items: [{ kind: 'file' }],
          },
        });

        // Component should handle the event without crashing
        expect(dropZone).toBeInTheDocument();
      }
    });

    it('should handle dragleave event', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const dropZone = screen.getByText(/Click to upload/i).closest('div')?.parentElement;

      if (dropZone) {
        fireEvent.dragLeave(dropZone);

        // Component should handle the event without crashing
        expect(dropZone).toBeInTheDocument();
      }
    });

    it('should handle drop event', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const dropZone = screen.getByText(/Click to upload/i).closest('div')?.parentElement;

      if (dropZone) {
        const file = new File(['test'], 'dropped.pdf', { type: 'application/pdf' });
        fireEvent.drop(dropZone, {
          dataTransfer: {
            files: [file],
          },
        });

        // Component should handle the event without crashing
        expect(dropZone).toBeInTheDocument();
      }
    });

    it('should show upload instructions in drop zone', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/Click to upload/i)).toBeInTheDocument();
      expect(screen.getByText(/or drag and drop/i)).toBeInTheDocument();
      const pdfTexts = screen.getAllByText(/PDF, DOCX, or TXT/i);
      expect(pdfTexts.length).toBeGreaterThan(0);
    });
  });

  describe('Form Submission', () => {
    it('should disable upload button when no file is selected', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });
      const uploadButton = screen.getByRole('button', { name: /upload/i });
      expect(uploadButton).toBeDisabled();
    });

    it('should disable upload button when no title is provided', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/Selected: test.pdf/i)).toBeInTheDocument();
      });

      const titleInput = screen.getByPlaceholderText('Enter document title') as HTMLInputElement;
      await user.clear(titleInput);

      await waitFor(() => {
        const uploadButton = screen.getByRole('button', { name: /upload/i });
        expect(uploadButton).toBeDisabled();
      });
    });

    it('should enable upload button when file and title are provided', async () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        const uploadButton = screen.getByRole('button', { name: /upload/i });
        expect(uploadButton).not.toBeDisabled();
      });
    });

    it('should call mutateAsync on form submission', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        expect(screen.getByText(/Selected: test.pdf/i)).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          file,
          title: 'test',
          description: undefined,
        });
      });
    });

    it('should include description if provided', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      const descInput = screen.getByPlaceholderText('Enter document description');
      await user.type(descInput, 'Test description');

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          file,
          title: 'test',
          description: 'Test description',
        });
      });
    });

    it('should call onSuccess with document ID on successful upload', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue({ id: 'doc-456', title: 'Success' });

      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith('doc-456');
      });
    });

    it('should call onClose on successful upload', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(defaultProps.onClose).toHaveBeenCalled();
      });
    });

    it('should show error message on upload failure', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockRejectedValue(new Error('Upload failed'));

      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText('Upload failed')).toBeInTheDocument();
      });
    });

    it('should show generic error message for non-Error failures', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockRejectedValue('String error');

      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to upload document')).toBeInTheDocument();
      });
    });

    it('should disable buttons during upload', async () => {
      vi.mocked(useDocumentsHook.useUploadDocument).mockReturnValue({
        ...mockUploadDocument,
        isPending: true,
      } as any);

      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      await waitFor(() => {
        const uploadButton = screen.getByRole('button', { name: /uploading.../i });
        const cancelButton = screen.getByRole('button', { name: /cancel/i });
        expect(uploadButton).toBeDisabled();
        expect(cancelButton).toBeDisabled();
      });
    });

    it('should show "Uploading..." text during upload', () => {
      vi.mocked(useDocumentsHook.useUploadDocument).mockReturnValue({
        ...mockUploadDocument,
        isPending: true,
      } as any);

      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });
  });

  describe('Modal Interaction', () => {
    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('should clear error when modal is opened', () => {
      const { rerender } = render(<UploadModal {...defaultProps} open={false} />, {
        wrapper: createWrapper(),
      });

      rerender(<UploadModal {...defaultProps} open={true} />);

      expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing onSuccess callback', async () => {
      const user = userEvent.setup();
      render(<UploadModal {...defaultProps} onSuccess={undefined} />, {
        wrapper: createWrapper(),
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      // Should not throw error
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });
    });

    it('should handle empty file drop', () => {
      render(<UploadModal {...defaultProps} />, { wrapper: createWrapper() });

      const dropZone = screen.getByText(/Click to upload/i).closest('div')?.parentElement;

      if (dropZone) {
        fireEvent.drop(dropZone, {
          dataTransfer: {
            files: [],
          },
        });

        expect(screen.queryByText(/Selected:/i)).not.toBeInTheDocument();
      }
    });
  });
});
