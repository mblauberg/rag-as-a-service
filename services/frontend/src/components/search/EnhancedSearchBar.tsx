import React, { useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, ChevronDownIcon, CheckIcon } from '@radix-ui/react-icons';
import { Cpu } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { Model } from '../../types';
import { abbreviateModelName, groupModelsByProvider } from '../../utils/modelUtils';

interface EnhancedSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  selectedModel: string | null;
  onModelChange: (model: string) => void;
  models: Model[];
  modelsLoading: boolean;
  autoFocus?: boolean;
  placeholder?: string;
}

/**
 * Enhanced SearchBar component with integrated model selector.
 *
 * Features:
 * - Press "/" to focus from anywhere
 * - Press "Escape" to clear and blur
 * - Glassmorphism styling with backdrop-blur
 * - Integrated model dropdown on right side
 */
export const EnhancedSearchBar: React.FC<EnhancedSearchBarProps> = ({
  value,
  onChange,
  selectedModel,
  onModelChange,
  models,
  modelsLoading,
  autoFocus = false,
  placeholder = 'Search documents...'
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus search on "/" key
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }

      // Clear on Escape
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        onChange('');
        inputRef.current?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onChange]);

  // Get current model for display
  const currentModel = models.find(m => m.name === selectedModel);
  const displayName = currentModel
    ? abbreviateModelName(currentModel.display_name)
    : 'Select model';

  // Group models by provider
  const groupedModels = groupModelsByProvider(models);
  const providerOrder = ['ollama', 'openai', 'anthropic', 'google'];

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="
            w-full pl-14 pr-48 py-4 text-lg
            bg-white/70 backdrop-blur-md
            border border-gray-200/50
            rounded-full shadow-lg
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400
          "
        />

        {/* Model Dropdown */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2">
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button
                className="
                  flex items-center gap-2 px-3 py-2
                  bg-white/70 backdrop-blur-md
                  border border-gray-200/50
                  rounded-full
                  hover:bg-white/90
                  transition-all duration-200
                  text-sm font-medium text-gray-700
                "
                disabled={modelsLoading}
              >
                <Cpu className="h-4 w-4" />
                <span>{modelsLoading ? 'Loading...' : displayName}</span>
                <ChevronDownIcon className="h-3 w-3" />
              </button>
            </DropdownMenu.Trigger>

            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="
                  min-w-[320px] max-h-[400px] overflow-y-auto
                  bg-white/90 backdrop-blur-md
                  border border-gray-200/50
                  rounded-lg shadow-lg
                  p-2
                "
                sideOffset={8}
                align="end"
              >
                {providerOrder.map((provider, idx) => {
                  const providerModels = groupedModels[provider];
                  if (!providerModels || providerModels.length === 0) return null;

                  return (
                    <React.Fragment key={provider}>
                      {idx > 0 && <DropdownMenu.Separator className="h-px bg-gray-200 my-2" />}

                      <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                        {provider}
                      </div>

                      {providerModels.map((model) => (
                        <DropdownMenu.Item
                          key={model.name}
                          className="
                            px-3 py-2.5 rounded-md
                            hover:bg-gray-100/80
                            cursor-pointer
                            outline-none
                            transition-colors
                          "
                          onSelect={() => onModelChange(model.name)}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-gray-900">
                                  {model.display_name}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {model.size}
                                </span>
                              </div>
                              <p className="text-xs text-gray-600 mt-0.5">
                                {model.description}
                              </p>
                            </div>
                            {selectedModel === model.name && (
                              <CheckIcon className="h-4 w-4 text-primary-600 flex-shrink-0 mt-1" />
                            )}
                          </div>
                        </DropdownMenu.Item>
                      ))}
                    </React.Fragment>
                  );
                })}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
      </div>
    </div>
  );
};
