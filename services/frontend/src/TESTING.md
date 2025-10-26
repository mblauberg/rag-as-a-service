# Frontend Testing Guidelines

## Test Organization

Tests are organized in `__tests__` directories alongside the code they test:

- `src/utils/__tests__/` - Utility function tests
- `src/components/search/__tests__/` - Search component tests
- `src/components/documents/__tests__/` - Document component tests
- `src/components/upload/__tests__/` - Upload component tests

## Running Tests

```bash
npm test              # Run tests in watch mode
npm run test:ui       # Run tests with Vitest UI
npm run test:coverage # Run tests with coverage report
```

## Test Structure

### Utility Tests
- Located in `src/utils/__tests__/`
- Test pure functions with clear inputs and outputs
- Use descriptive test names that explain the expected behavior

Example:
```typescript
describe('formatBytes', () => {
  it('should format 0 bytes', () => {
    expect(formatBytes(0)).toBe('0 B');
  });
});
```

### Component Tests
- Located in `src/components/[component]/__tests__/`
- Test user interactions and component behavior
- Mock external dependencies (API calls, hooks)
- Use @testing-library/react for rendering and queries

Example:
```typescript
import { render, screen } from '@testing-library/react';
import { DocumentCard } from '../DocumentCard';

describe('DocumentCard', () => {
  it('should render the document title', () => {
    render(<DocumentCard document={mockDocument} />);
    expect(screen.getByText('Test Document')).toBeInTheDocument();
  });
});
```

## Testing Best Practices

### 1. Use Descriptive Test Names
- Test names should describe the expected behavior
- Use "should" statements: `it('should render loading state')`

### 2. Group Related Tests
- Use `describe` blocks to organize related tests
- Group by feature or functionality

### 3. Mock External Dependencies
```typescript
vi.mock('@/services/api', () => ({
  fetchDocuments: vi.fn(),
}));
```

### 4. Test User Interactions
```typescript
const user = userEvent.setup();
await user.click(screen.getByRole('button'));
```

### 5. Verify Accessibility
- Use semantic queries: `getByRole`, `getByLabelText`
- Avoid `getByTestId` unless necessary

## Common Patterns

### Testing Async Operations
```typescript
it('should fetch and display data', async () => {
  render(<Component />);
  await screen.findByText('Loaded Data');
  expect(screen.getByText('Loaded Data')).toBeInTheDocument();
});
```

### Testing Forms
```typescript
const user = userEvent.setup();
await user.type(screen.getByLabelText('Search'), 'query');
await user.click(screen.getByRole('button', { name: 'Search' }));
```

### Mocking API Responses
```typescript
import { useQuery } from '@tanstack/react-query';
vi.mocked(useQuery).mockReturnValue({
  data: mockData,
  isLoading: false,
  error: null,
});
```

## Current Test Coverage

- **8 test files** with **160 tests passing** and **15 skipped**
- Tests cover utility functions, search, documents, and upload components
- All tests pass successfully

## Framework & Tools

- **Testing Framework**: Vitest
- **Component Testing**: @testing-library/react
- **User Interaction**: @testing-library/user-event
- **DOM Assertions**: @testing-library/jest-dom

## Notes

- Tests run in watch mode by default for rapid feedback
- Component tests may show warnings about Radix UI accessibility - these are expected in test environments
- Use `vi.fn()` for mocking functions
- Use `waitFor` or `findBy*` queries for async assertions
