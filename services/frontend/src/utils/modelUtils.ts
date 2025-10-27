import { Model } from '../types';

/** Abbreviate model display name for compact UI. */
export function abbreviateModelName(displayName: string): string {
  // "Llama 3.3 70B" -> "Llama 3.3"
  // "GPT-5" -> "GPT-5" (keep short)
  // "Claude Sonnet 4.5" -> "Sonnet 4.5"
  // "Gemini 2.5 Pro" -> "Gemini 2.5"

  // Claude models: extract everything after "Claude "
  if (displayName.startsWith('Claude ')) {
    return displayName.replace('Claude ', '');
  }

  // Remove size suffix (e.g., " 70B", " 8B")
  const withoutSize = displayName.replace(/\s+\d+B$/i, '');

  // If name is short (<=10 chars), keep as-is
  if (withoutSize.length <= 10) {
    return withoutSize;
  }

  // For Gemini, remove "Pro"/"Flash" suffix
  if (displayName.startsWith('Gemini')) {
    return displayName.replace(/ (Pro|Flash)$/i, '');
  }

  return withoutSize;
}

/** Group models by provider for dropdown menu. */
export function groupModelsByProvider(models: Model[]): Record<string, Model[]> {
  const grouped: Record<string, Model[]> = {};

  models.forEach(model => {
    if (!grouped[model.provider]) {
      grouped[model.provider] = [];
    }
    grouped[model.provider].push(model);
  });

  return grouped;
}
