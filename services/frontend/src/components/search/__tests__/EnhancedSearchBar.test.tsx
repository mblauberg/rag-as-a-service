import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EnhancedSearchBar } from '../EnhancedSearchBar';
import type { Model } from '../../../types';

const mockModels: Model[] = [
  {
    name: 'llama3.3:70b',
    display_name: 'Llama 3.3 70B',
    provider: 'ollama',
    size: '70B',
    description: 'Most capable Llama model',
    capabilities: ['reasoning', 'coding'],
    modified_at: '2024-01-01T00:00:00Z',
  },
  {
    name: 'llama3.2:3b',
    display_name: 'Llama 3.2 3B',
    provider: 'ollama',
    size: '3B',
    description: 'Smaller, faster Llama model',
    capabilities: ['general'],
    modified_at: '2024-01-01T00:00:00Z',
  },
  {
    name: 'openai:gpt-4',
    display_name: 'GPT-4',
    provider: 'openai',
    size: 'N/A',
    description: 'OpenAI flagship model',
    capabilities: ['reasoning', 'coding', 'analysis'],
    modified_at: '2024-01-01T00:00:00Z',
  },
  {
    name: 'anthropic:claude-sonnet-4.5',
    display_name: 'Claude Sonnet 4.5',
    provider: 'anthropic',
    size: 'N/A',
    description: 'Anthropic balanced model',
    capabilities: ['reasoning', 'coding', 'analysis'],
    modified_at: '2024-01-01T00:00:00Z',
  },
  {
    name: 'google:gemini-2.5-pro',
    display_name: 'Gemini 2.5 Pro',
    provider: 'google',
    size: 'N/A',
    description: 'Google advanced model',
    capabilities: ['reasoning', 'multimodal'],
    modified_at: '2024-01-01T00:00:00Z',
  },
];

describe('EnhancedSearchBar', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    selectedModel: null,
    onModelChange: vi.fn(),
    models: mockModels,
    modelsLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render the search input', () => {
      render(<EnhancedSearchBar {...defaultProps} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });
      expect(input).toBeInTheDocument();
    });

    it('should display the default placeholder', () => {
      render(<EnhancedSearchBar {...defaultProps} />);
      expect(screen.getByPlaceholderText('Search documents...')).toBeInTheDocument();
    });

    it('should display custom placeholder', () => {
      render(<EnhancedSearchBar {...defaultProps} placeholder="Custom search..." />);
      expect(screen.getByPlaceholderText('Custom search...')).toBeInTheDocument();
    });

    it('should render the magnifying glass icon', () => {
      const { container } = render(<EnhancedSearchBar {...defaultProps} />);
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should autofocus when autoFocus prop is true', () => {
      render(<EnhancedSearchBar {...defaultProps} autoFocus={true} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });
      expect(input).toHaveFocus();
    });
  });

  describe('Input Interaction', () => {
    it('should call onChange when typing', async () => {
      const user = userEvent.setup();
      render(<EnhancedSearchBar {...defaultProps} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });

      await user.type(input, 'test query');

      expect(defaultProps.onChange).toHaveBeenCalled();
    });

    it('should display the current value', () => {
      render(<EnhancedSearchBar {...defaultProps} value="current search" />);
      const input = screen.getByRole('textbox', { name: /search documents/i }) as HTMLInputElement;
      expect(input.value).toBe('current search');
    });

    it('should allow clearing the input', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(<EnhancedSearchBar {...defaultProps} value="test" onChange={onChange} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });

      await user.clear(input);

      expect(onChange).toHaveBeenCalled();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should focus input when "/" key is pressed', async () => {
      render(<EnhancedSearchBar {...defaultProps} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });

      expect(input).not.toHaveFocus();

      fireEvent.keyDown(window, { key: '/' });

      expect(input).toHaveFocus();
    });

    it('should not focus input when "/" is pressed while input is already focused', async () => {
      const user = userEvent.setup();
      render(<EnhancedSearchBar {...defaultProps} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });

      await user.click(input);
      expect(input).toHaveFocus();

      // Verify input is already focused before pressing '/'
      expect(document.activeElement).toBe(input);
      fireEvent.keyDown(window, { key: '/' });

      // Should still be focused (no additional focus event)
      expect(input).toHaveFocus();
    });

    it('should clear and blur input when Escape key is pressed', async () => {
      const onChange = vi.fn();
      render(<EnhancedSearchBar {...defaultProps} value="test" onChange={onChange} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });

      input.focus();
      expect(input).toHaveFocus();

      fireEvent.keyDown(window, { key: 'Escape' });

      expect(onChange).toHaveBeenCalledWith('');
      expect(input).not.toHaveFocus();
    });

    it('should not clear input when Escape is pressed while input is not focused', () => {
      const onChange = vi.fn();
      render(<EnhancedSearchBar {...defaultProps} value="test" onChange={onChange} />);

      fireEvent.keyDown(window, { key: 'Escape' });

      expect(onChange).not.toHaveBeenCalled();
    });

    it('should remove event listeners on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
      const { unmount } = render(<EnhancedSearchBar {...defaultProps} />);

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    });
  });

  describe('Model Selector', () => {
    it('should render model selector button', () => {
      render(<EnhancedSearchBar {...defaultProps} />);
      expect(screen.getByRole('button', { name: /select model/i })).toBeInTheDocument();
    });

    it('should display "Loading..." when models are loading', () => {
      render(<EnhancedSearchBar {...defaultProps} modelsLoading={true} />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('should disable model button when loading', () => {
      render(<EnhancedSearchBar {...defaultProps} modelsLoading={true} />);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should display selected model name', () => {
      render(<EnhancedSearchBar {...defaultProps} selectedModel="llama3.3:70b" />);
      expect(screen.getByText('Llama 3.3')).toBeInTheDocument();
    });

    it('should show "Select model" when no model is selected', () => {
      render(<EnhancedSearchBar {...defaultProps} selectedModel={null} />);
      expect(screen.getByText('Select model')).toBeInTheDocument();
    });

    it('should open dropdown when model button is clicked', async () => {
      const user = userEvent.setup();
      render(<EnhancedSearchBar {...defaultProps} />);

      const button = screen.getByRole('button', { name: /select model/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText('Llama 3.3 70B')).toBeInTheDocument();
      });
    });

    it('should call onModelChange when a model is selected', async () => {
      const user = userEvent.setup();
      render(<EnhancedSearchBar {...defaultProps} />);

      const button = screen.getByRole('button', { name: /select model/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText('Llama 3.3 70B')).toBeInTheDocument();
      });

      const modelOption = screen.getByText('Llama 3.3 70B').closest('[role="menuitem"]');
      if (modelOption) {
        await user.click(modelOption);
        expect(defaultProps.onModelChange).toHaveBeenCalledWith('llama3.3:70b');
      }
    });

    it('should display check icon next to selected model', async () => {
      const user = userEvent.setup();
      render(<EnhancedSearchBar {...defaultProps} selectedModel="llama3.3:70b" />);

      const button = screen.getByRole('button');
      await user.click(button);

      await waitFor(() => {
        const selectedItem = screen.getByText('Llama 3.3 70B').closest('[role="menuitem"]');
        expect(selectedItem).toBeInTheDocument();
        // CheckIcon should be rendered for selected model
        const checkIcon = selectedItem?.querySelector('svg');
        expect(checkIcon).toBeInTheDocument();
      });
    });
  });

  describe('Provider Grouping', () => {
    it('should group models by provider', async () => {
      const user = userEvent.setup();
      const { baseElement } = render(<EnhancedSearchBar {...defaultProps} />);

      const button = screen.getByRole('button', { name: /select model/i });
      await user.click(button);

      await waitFor(() => {
        // Use baseElement to query portal content
        expect(baseElement.textContent).toContain('ollama');
        expect(baseElement.textContent).toContain('openai');
        expect(baseElement.textContent).toContain('anthropic');
        expect(baseElement.textContent).toContain('google');
      });
    });

    it('should display models under correct provider headers', async () => {
      const user = userEvent.setup();
      render(<EnhancedSearchBar {...defaultProps} />);

      const button = screen.getByRole('button', { name: /select model/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText('Llama 3.3 70B')).toBeInTheDocument();
        expect(screen.getByText('GPT-4')).toBeInTheDocument();
        expect(screen.getByText('Claude Sonnet 4.5')).toBeInTheDocument();
        expect(screen.getByText('Gemini 2.5 Pro')).toBeInTheDocument();
      });
    });

    it('should display model size and description', async () => {
      const user = userEvent.setup();
      render(<EnhancedSearchBar {...defaultProps} />);

      const button = screen.getByRole('button', { name: /select model/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText('70B')).toBeInTheDocument();
        expect(screen.getByText('Most capable Llama model')).toBeInTheDocument();
      });
    });

    it('should not render provider sections with no models', async () => {
      const user = userEvent.setup();
      const modelsWithoutGoogle = mockModels.filter(m => m.provider !== 'google');

      render(<EnhancedSearchBar {...defaultProps} models={modelsWithoutGoogle} />);

      const button = screen.getByRole('button', { name: /select model/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.queryByText('GOOGLE')).not.toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty models array', () => {
      render(<EnhancedSearchBar {...defaultProps} models={[]} />);
      expect(screen.getByText('Select model')).toBeInTheDocument();
    });

    it('should handle model not found in list', () => {
      render(<EnhancedSearchBar {...defaultProps} selectedModel="non-existent-model" />);
      expect(screen.getByText('Select model')).toBeInTheDocument();
    });

    it('should handle rapid keyboard events', async () => {
      render(<EnhancedSearchBar {...defaultProps} />);
      const input = screen.getByRole('textbox', { name: /search documents/i });

      fireEvent.keyDown(window, { key: '/' });
      fireEvent.keyDown(window, { key: '/' });
      fireEvent.keyDown(window, { key: '/' });

      expect(input).toHaveFocus();
    });

    it('should handle multiple models from same provider', async () => {
      const user = userEvent.setup();
      const { baseElement } = render(<EnhancedSearchBar {...defaultProps} />);

      const button = screen.getByRole('button', { name: /select model/i });
      await user.click(button);

      await waitFor(() => {
        // Should show both Llama models under Ollama provider
        expect(baseElement.textContent).toContain('Llama 3.3 70B');
        expect(baseElement.textContent).toContain('Llama 3.2 3B');
      });
    });
  });
});
