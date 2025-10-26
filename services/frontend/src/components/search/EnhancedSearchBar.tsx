import React, { useEffect, useRef } from 'react';
import { MagnifyingGlassIcon } from '@radix-ui/react-icons';
import { Cpu } from 'lucide-react';
import { Model } from '@/types';
import { abbreviateModelName, groupModelsByProvider } from '@/utils/modelUtils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';

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
 * - shadcn/ui Select component for model selection
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
  const providerOrder = ['openai', 'anthropic', 'google'];

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <div className="relative">
        <div className="absolute left-6 top-1/2 -translate-y-1/2 z-10">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" style={{ width: '20px', height: '20px' }} />
        </div>

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          aria-label="Search documents by content or title"
          className="
            w-full pl-14 pr-48 py-4 text-lg
            bg-white/70 backdrop-blur-md
            border border-gray-200/50
            rounded-full shadow-lg
            focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400
          "
        />

        {/* Model Select */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2">
          {modelsLoading ? (
            <Skeleton className="h-10 w-40" />
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 bg-white/70 backdrop-blur-md border border-gray-200/50 rounded-full">
              <Cpu className="h-4 w-4 text-gray-500" />
              <Select
                value={selectedModel || undefined}
                onValueChange={(value) => onModelChange(value)}
              >
                <SelectTrigger className="border-none bg-transparent h-auto p-0 focus:ring-0 focus:ring-offset-0 w-32">
                  <SelectValue placeholder="Select model">
                    <span className="text-sm font-medium text-gray-700">
                      {displayName}
                    </span>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {providerOrder.map((provider, idx) => {
                    const providerModels = groupedModels[provider];
                    if (!providerModels || providerModels.length === 0) return null;

                    return (
                      <React.Fragment key={provider}>
                        {idx > 0 && <SelectSeparator />}
                        <SelectGroup>
                          <SelectLabel className="text-xs font-semibold text-gray-500 uppercase">
                            {provider}
                          </SelectLabel>
                          {providerModels.map((model) => (
                            <SelectItem key={model.name} value={model.name}>
                              <div className="flex items-start gap-2">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-gray-900">
                                      {model.display_name}
                                    </span>
                                    {model.size && model.size !== 'N/A' && (
                                      <span className="text-xs text-gray-500">
                                        {model.size}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-gray-600 mt-0.5 truncate">
                                    {model.description}
                                  </p>
                                </div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </React.Fragment>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
