/**
 * Tests for UploadModal component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/utils';
import { UploadModal } from '../UploadModal';

// Mock useUploadDocument hook
const mockMutateAsync = vi.fn();
const mockReset = vi.fn();

vi.mock('../../hooks/useDocuments', () => ({
  useUploadDocument: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isSuccess: false,
    error: null,
    reset: mockReset,
  }),
}));

describe('UploadModal', () => {
  const mockOnClose = vi.fn();
  const mockOnUploadSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    renderWithProviders(
      <UploadModal isOpen={false} onClose={mockOnClose} />
    );

    expect(screen.queryByText('Upload Document')).not.toBeInTheDocument();
  });

  it('renders when isOpen is true', () => {
    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    expect(screen.getByText('Upload Document')).toBeInTheDocument();
  });

  it('shows dropzone by default', () => {
    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    expect(screen.getByText(/drag and drop your file here/i)).toBeInTheDocument();
    expect(screen.getByText(/or click to browse/i)).toBeInTheDocument();
    expect(screen.getByText(/Supported formats: PDF, DOCX, TXT/i)).toBeInTheDocument();
  });

  it('shows file preview after file selection', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    // Create a test file
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });

    // Find the file input and upload
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    // File preview should be shown
    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    });
  });

  it('auto-fills title from filename', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    const file = new File(['content'], 'my-document.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    await waitFor(() => {
      const titleInput = screen.getByLabelText(/title/i) as HTMLInputElement;
      expect(titleInput.value).toBe('my-document');
    });
  });

  it('allows removing selected file', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    // Wait for file to appear
    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    });

    // Click remove button
    const removeButton = screen.getByLabelText('Remove file');
    await user.click(removeButton);

    // Dropzone should be shown again
    await waitFor(() => {
      expect(screen.getByText(/drag and drop your file here/i)).toBeInTheDocument();
    });
  });

  it('shows validation error when uploading without file', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    const uploadButton = screen.getByRole('button', { name: /upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText('Please select a file to upload')).toBeInTheDocument();
    });
  });

  it('shows validation error when uploading without title', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    // Upload file
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    // Clear the auto-filled title
    await waitFor(() => {
      const titleInput = screen.getByLabelText(/title/i);
      expect(titleInput).toBeInTheDocument();
    });

    const titleInput = screen.getByLabelText(/title/i);
    await user.clear(titleInput);

    // Try to upload
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter a title')).toBeInTheDocument();
    });
  });

  it('calls mutateAsync with correct data on upload', async () => {
    const user = userEvent.setup();

    mockMutateAsync.mockResolvedValue({
      id: '123',
      title: 'Test Document',
      description: 'Test description',
    });

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    // Upload file
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    // Fill in form
    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    });

    const titleInput = screen.getByLabelText(/title/i);
    const descriptionInput = screen.getByLabelText(/description/i);

    await user.clear(titleInput);
    await user.type(titleInput, 'Test Document');
    await user.type(descriptionInput, 'Test description');

    // Click upload
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        file: expect.any(File),
        title: 'Test Document',
        description: 'Test description',
      });
    });
  });

  it('calls onUploadSuccess after successful upload', async () => {
    const user = userEvent.setup();

    const mockResult = {
      id: '123',
      title: 'Test Document',
    };

    mockMutateAsync.mockResolvedValue(mockResult);

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} onUploadSuccess={mockOnUploadSuccess} />
    );

    // Upload file
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    // Wait for title input
    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    });

    // Click upload
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockOnUploadSuccess).toHaveBeenCalledWith(mockResult);
    });
  });

  it('closes modal on close button click', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    const closeButton = screen.getByLabelText('Close modal');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('closes modal on cancel button click', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('closes modal on backdrop click', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    // Find backdrop (the div with backdrop-blur-sm class)
    const backdrop = screen.getByRole('dialog').previousElementSibling as HTMLElement;
    await user.click(backdrop);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows form fields after file selection', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });

    const titleInput = screen.getByLabelText(/title/i);
    const descriptionInput = screen.getByLabelText(/description/i);

    expect(titleInput).toHaveAttribute('type', 'text');
    expect(descriptionInput).toHaveAttribute('rows', '3');
  });

  it('has proper accessibility attributes', () => {
    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'upload-modal-title');

    const title = screen.getByText('Upload Document');
    expect(title).toHaveAttribute('id', 'upload-modal-title');
  });

  it('accepts file drops', async () => {
    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    // Get the dropzone input
    const input = screen.getByLabelText('File upload');
    expect(input).toHaveAttribute('type', 'file');
  });

  it('resets form when modal closes', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    // Upload file and fill form
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByLabelText('Close modal');
    await user.click(closeButton);

    expect(mockReset).toHaveBeenCalled();
  });

  it('handles description as optional field', async () => {
    const user = userEvent.setup();

    mockMutateAsync.mockResolvedValue({ id: '123' });

    renderWithProviders(
      <UploadModal isOpen={true} onClose={mockOnClose} />
    );

    // Upload file
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('File upload');
    await user.upload(input, file);

    // Wait for form
    await waitFor(() => {
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    });

    // Don't fill description, just upload
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          description: undefined,
        })
      );
    });
  });
});
