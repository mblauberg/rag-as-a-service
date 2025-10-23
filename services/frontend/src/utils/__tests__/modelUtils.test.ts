import { describe, it, expect } from 'vitest';
import { abbreviateModelName, groupModelsByProvider } from '../modelUtils';
import { Model } from '../../types';

describe('abbreviateModelName', () => {
  it('abbreviates Llama models', () => {
    expect(abbreviateModelName('Llama 3.3 70B')).toBe('Llama 3.3');
  });

  it('keeps short names as-is', () => {
    expect(abbreviateModelName('GPT-5')).toBe('GPT-5');
    expect(abbreviateModelName('GPT-5 Mini')).toBe('GPT-5 Mini');
  });

  it('abbreviates Claude Sonnet models', () => {
    expect(abbreviateModelName('Claude Sonnet 4.5')).toBe('Sonnet 4.5');
  });

  it('abbreviates Gemini models', () => {
    expect(abbreviateModelName('Gemini 2.5 Pro')).toBe('Gemini 2.5');
  });
});

describe('groupModelsByProvider', () => {
  const models: Model[] = [
    {
      name: 'llama3.3:70b',
      display_name: 'Llama 3.3 70B',
      provider: 'ollama',
      size: '70B',
      description: 'Test',
      capabilities: [],
      modified_at: '2025-10-24T10:00:00Z'
    },
    {
      name: 'openai:gpt-5',
      display_name: 'GPT-5',
      provider: 'openai',
      size: 'N/A',
      description: 'Test',
      capabilities: [],
      modified_at: '2025-10-24T10:00:00Z'
    }
  ];

  it('groups models by provider', () => {
    const grouped = groupModelsByProvider(models);

    expect(grouped.ollama).toHaveLength(1);
    expect(grouped.openai).toHaveLength(1);
    expect(grouped.ollama[0].name).toBe('llama3.3:70b');
  });

  it('handles empty model list', () => {
    const grouped = groupModelsByProvider([]);
    expect(Object.keys(grouped)).toHaveLength(0);
  });
});
