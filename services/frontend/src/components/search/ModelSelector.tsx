import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import type { Model } from '../../types';

interface ModelSelectorProps {
  selectedModel: string | null;
  onModelChange: (model: string) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  onModelChange
}) => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await api.listModels();
        setModels(response.models);

        // Set default model if none selected
        if (!selectedModel && response.models.length > 0) {
          const savedModel = localStorage.getItem('selectedModel');
          const defaultModel = savedModel || response.models[0].name;
          onModelChange(defaultModel);
        }
      } catch (err) {
        setError('Failed to load models');
        console.error('Error fetching models:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, [selectedModel, onModelChange]);

  const handleModelChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const model = event.target.value;
    onModelChange(model);
    localStorage.setItem('selectedModel', model);
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Model</label>
        <div className="h-10 w-48 bg-gray-100 animate-pulse rounded-md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">{error}</div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="model-select" className="text-sm font-medium text-gray-700">
        Model
      </label>
      <select
        id="model-select"
        value={selectedModel || ''}
        onChange={handleModelChange}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {models.map((model) => (
          <option key={model.name} value={model.name}>
            {model.name} • {model.size}
          </option>
        ))}
      </select>
    </div>
  );
};
