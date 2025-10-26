import { describe, it, expect } from 'vitest';
import { abbreviateModelName, groupModelsByProvider } from '../modelUtils';
import { Model } from '../../types';

describe('abbreviateModelName', () => {
  it('keeps short names as-is', () => {
    expect(abbreviateModelName('GPT-5')).toBe('GPT-5');
    expect(abbreviateModelName('GPT-5 Mini')).toBe('GPT-5 Mini');
  });

  it('abbreviates Claude Sonnet models', () => {
    expect(abbreviateModelName('Claude Sonnet 4.5')).toBe('Sonnet 4.5');
  });

  it('abbreviates Claude Opus models', () => {
    expect(abbreviateModelName('Claude Opus 4.1')).toBe('Opus 4.1');
  });

  it('abbreviates Gemini models', () => {
    expect(abbreviateModelName('Gemini 2.5 Pro')).toBe('Gemini 2.5');
    expect(abbreviateModelName('Gemini 2.5 Flash')).toBe('Gemini 2.5');
  });
});

describe('groupModelsByProvider', () => {
  const models: Model[] = [
    {
      name: 'openai:gpt-5',
      display_name: 'GPT-5',
      provider: 'openai',
      size: 'N/A',
      description: 'Most capable model',
      capabilities: ['reasoning', 'coding'],
      modified_at: '2025-10-24T10:00:00Z'
    },
    {
      name: 'anthropic:claude-sonnet-4-5',
      display_name: 'Claude Sonnet 4.5',
      provider: 'anthropic',
      size: 'N/A',
      description: 'Balanced performance',
      capabilities: ['reasoning', 'coding'],
      modified_at: '2025-10-24T10:00:00Z'
    }
  ];

  it('groups models by provider', () => {
    const grouped = groupModelsByProvider(models);

    expect(grouped.openai).toHaveLength(1);
    expect(grouped.anthropic).toHaveLength(1);
    expect(grouped.openai[0].name).toBe('openai:gpt-5');
  });

  it('handles empty model list', () => {
    const grouped = groupModelsByProvider([]);
    expect(Object.keys(grouped)).toHaveLength(0);
  });
});
