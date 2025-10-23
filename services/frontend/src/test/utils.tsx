/**
 * Test utilities for rendering components with providers
 */
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

/**
 * Create a new QueryClient for testing
 * Disables retries and logging for cleaner test output
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Wrapper component with all necessary providers
 */
interface AllProvidersProps {
  children: React.ReactNode;
}

export function createWrapper(queryClient?: QueryClient) {
  const client = queryClient || createTestQueryClient();

  return function AllProviders({ children }: AllProvidersProps) {
    return (
      <QueryClientProvider client={client}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    );
  };
}

/**
 * Custom render function that includes providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { queryClient?: QueryClient }
) {
  const { queryClient, ...renderOptions } = options || {};

  return render(ui, {
    wrapper: createWrapper(queryClient),
    ...renderOptions,
  });
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react';
