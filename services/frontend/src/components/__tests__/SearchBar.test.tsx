/**
 * Tests for SearchBar component
 */
import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/utils';
import { SearchBar } from '../search/SearchBar';

describe('SearchBar', () => {
  it('renders correctly with default placeholder', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', 'Search documents...');
  });

  it('renders with custom placeholder', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} placeholder="Custom placeholder" />
    );

    const input = screen.getByLabelText('Search query');
    expect(input).toHaveAttribute('placeholder', 'Custom placeholder');
  });

  it('calls onSearch when Enter key is pressed', async () => {
    const user = userEvent.setup();
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');

    // Type a query
    await user.type(input, 'test query');
    expect(input).toHaveValue('test query');

    // Press Enter
    await user.keyboard('{Enter}');

    // Verify onSearch was called with trimmed query
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('test query');
      expect(mockOnSearch).toHaveBeenCalledTimes(1);
    });
  });

  it('trims whitespace from query before calling onSearch', async () => {
    const user = userEvent.setup();
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');

    // Type query with leading/trailing spaces
    await user.type(input, '  test query  ');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('test query');
    });
  });

  it('does not call onSearch with empty query', async () => {
    const user = userEvent.setup();
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');

    // Press Enter without typing
    await user.click(input);
    await user.keyboard('{Enter}');

    expect(mockOnSearch).not.toHaveBeenCalled();
  });

  it('does not call onSearch with only whitespace', async () => {
    const user = userEvent.setup();
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');

    // Type only spaces
    await user.type(input, '   ');
    await user.keyboard('{Enter}');

    expect(mockOnSearch).not.toHaveBeenCalled();
  });

  it('shows loading state when isLoading is true', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} isLoading={true} />
    );

    const input = screen.getByLabelText('Search query');

    // Input should be disabled during loading
    expect(input).toBeDisabled();

    // Loading spinner should be visible (check for aria-hidden attribute)
    const spinner = screen.getByRole('img', { hidden: true });
    expect(spinner).toBeInTheDocument();

    // Screen reader announcement
    expect(screen.getByText('Searching...')).toBeInTheDocument();
  });

  it('disables input during loading', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} isLoading={true} />
    );

    const input = screen.getByLabelText('Search query');
    expect(input).toBeDisabled();
  });

  it('prevents submission during loading', async () => {
    const user = userEvent.setup();
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} isLoading={true} />
    );

    const input = screen.getByLabelText('Search query');

    // Try to type (should not work because input is disabled)
    await user.click(input);
    await user.keyboard('test{Enter}');

    // onSearch should not be called
    expect(mockOnSearch).not.toHaveBeenCalled();
  });

  it('updates input value as user types', async () => {
    const user = userEvent.setup();
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');

    await user.type(input, 'semantic search');

    expect(input).toHaveValue('semantic search');
  });

  it('allows multiple searches', async () => {
    const user = userEvent.setup();
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');

    // First search
    await user.type(input, 'first query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('first query');
    });

    // Clear and second search
    await user.clear(input);
    await user.type(input, 'second query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('second query');
      expect(mockOnSearch).toHaveBeenCalledTimes(2);
    });
  });

  it('applies custom className', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} className="custom-class" />
    );

    const form = screen.getByLabelText('Search query').closest('form');
    expect(form).toHaveClass('custom-class');
  });

  it('shows search hint text', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    expect(screen.getByText('Press Enter to search or type to begin')).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} />
    );

    const input = screen.getByLabelText('Search query');

    expect(input).toHaveAttribute('type', 'text');
    expect(input).toHaveAttribute('aria-label', 'Search query');
  });

  it('has accessibility attributes during loading', () => {
    const mockOnSearch = vi.fn();

    renderWithProviders(
      <SearchBar onSearch={mockOnSearch} isLoading={true} />
    );

    const input = screen.getByLabelText('Search query');

    expect(input).toHaveAttribute('aria-describedby', 'search-loading');
    expect(screen.getByText('Searching...')).toHaveClass('sr-only');
  });
});
