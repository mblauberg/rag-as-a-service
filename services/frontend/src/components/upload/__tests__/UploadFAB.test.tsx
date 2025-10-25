import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UploadFAB } from '../UploadFAB';

describe('UploadFAB', () => {
  it('should render FAB button', () => {
    render(<UploadFAB onClick={vi.fn()} />);

    const button = screen.getByRole('button', { name: /upload document/i });
    expect(button).toBeInTheDocument();
  });

  it('should call onClick when clicked', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();

    render(<UploadFAB onClick={onClick} />);

    const button = screen.getByRole('button', { name: /upload document/i });
    await user.click(button);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('should have proper accessibility label', () => {
    render(<UploadFAB onClick={vi.fn()} />);

    const button = screen.getByRole('button', { name: /upload document/i });
    expect(button).toHaveAttribute('aria-label', 'Upload document');
  });

  it('should render with fixed positioning classes', () => {
    const { container } = render(<UploadFAB onClick={vi.fn()} />);

    const wrapper = container.querySelector('.fixed');
    expect(wrapper).toBeInTheDocument();
    expect(wrapper).toHaveClass('bottom-8', 'right-8', 'z-50');
  });

  it('should render button with circular shape', () => {
    render(<UploadFAB onClick={vi.fn()} />);

    const button = screen.getByRole('button', { name: /upload document/i });
    expect(button).toHaveClass('rounded-full');
  });

  it('should render PlusIcon inside button', () => {
    render(<UploadFAB onClick={vi.fn()} />);

    const button = screen.getByRole('button', { name: /upload document/i });
    const icon = button.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should have shadow classes for elevation', () => {
    render(<UploadFAB onClick={vi.fn()} />);

    const button = screen.getByRole('button', { name: /upload document/i });
    expect(button).toHaveClass('shadow-lg');
  });

  it('should not be disabled by default', () => {
    render(<UploadFAB onClick={vi.fn()} />);

    const button = screen.getByRole('button', { name: /upload document/i });
    expect(button).not.toBeDisabled();
  });
});
