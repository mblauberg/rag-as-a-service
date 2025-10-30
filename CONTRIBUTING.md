# Contributing to RAaS

Thank you for your interest in contributing to RAaS (Retrieval-Augmented Generation as a Service)!

## Project Status

**Important**: This is a portfolio/academic project created as a final university assignment. While it demonstrates production-grade practices, **active development is not planned**.

However, contributions are welcome for:
- Bug fixes
- Documentation improvements
- Security patches
- Educational enhancements
- Learning examples

## Ways to Contribute

### 1. Reporting Bugs

Found a bug? Please [open an issue](../../issues/new?template=bug_report.md) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, etc.)
- Relevant logs or screenshots

### 2. Suggesting Features

Have an idea? [Submit a feature request](../../issues/new?template=feature_request.md) with:
- Problem statement
- Proposed solution
- Use case examples
- Implementation considerations

### 3. Improving Documentation

Documentation improvements are always welcome:
- Fix typos or unclear explanations
- Add examples or tutorials
- Improve API documentation
- Create diagrams or visual aids

### 4. Submitting Code

Want to contribute code? Great! Please follow these guidelines.

## Development Setup

### Prerequisites

- Docker 24.0+ with Docker Compose
- Python 3.13+ with Poetry
- Node.js 18+ with npm
- Git

### Getting Started

1. **Fork the repository**

```bash
# Fork via GitHub UI, then clone your fork
git clone https://github.com/YOUR_USERNAME/raas.git
cd raas
```

2. **Set up development environment**

```bash
# Backend (choose a service)
cd services/api
poetry install
poetry run pytest  # Run tests

# Frontend
cd services/frontend
npm install
npm test  # Run tests
```

3. **Start services locally**

```bash
# From project root
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d
```

4. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Code Standards

### Python Services

- **Type hints**: Required for all functions
- **Docstrings**: Google style for public APIs
- **Formatting**: Handled by Ruff
- **Type checking**: Must pass `mypy --strict`
- **Testing**: Pytest with meaningful test names

```python
# Good example
async def search_documents(
    query: str,
    limit: int = 10,
    threshold: float = 0.7
) -> list[SearchResult]:
    """Search documents using semantic similarity.

    Args:
        query: Natural language search query
        limit: Maximum number of results to return
        threshold: Minimum similarity score (0-1)

    Returns:
        List of search results ordered by relevance
    """
    # Implementation
```

### TypeScript/React

- **Type safety**: No `any` types without justification
- **Components**: Functional components with hooks
- **Testing**: React Testing Library for component tests
- **Formatting**: Prettier (runs automatically)

```typescript
// Good example
interface SearchProps {
  onSearch: (query: string) => Promise<void>;
  isLoading: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchProps) {
  // Implementation
}
```

## Testing Requirements

### Unit Tests

All new features must include tests:

```bash
# Python
cd services/api
poetry run pytest tests/ -v

# TypeScript
cd services/frontend
npm test
```

### Integration Tests

For changes affecting multiple services:

```bash
./tests/integration/test_full_workflow.sh
```

### Test Coverage

- Aim for >80% coverage on new code
- Don't sacrifice quality for coverage metrics
- Focus on meaningful tests, not just coverage numbers

## Pull Request Process

1. **Ensure all tests pass**

```bash
# Type checking
cd services/api && poetry run mypy app/
cd services/frontend && npx tsc --noEmit

# Linting
cd services/api && poetry run ruff check app/
cd services/frontend && npm run lint

# Tests
poetry run pytest
npm test
```

2. **Update documentation**
   - Add/update README sections if needed
   - Update API documentation for endpoint changes
   - Add inline comments for complex logic

3. **Create a descriptive PR**
   - Use the PR template
   - Link related issues
   - Explain the "why" not just the "what"
   - Add screenshots for UI changes

4. **Be responsive to feedback**
   - Respond to review comments
   - Make requested changes
   - Keep discussions professional and constructive

## Commit Message Guidelines

Follow conventional commits:

```
type(scope): brief description

- Detailed explanation if needed
- Can span multiple lines
- Use bullet points for clarity

Closes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(search): add cross-encoder reranking

- Implements bi-encoder + cross-encoder pipeline
- Improves precision@10 by 15%
- Adds configuration for reranker model

Closes #42

---

fix(api): handle empty document upload

Validates file size > 0 before processing to prevent
500 errors on empty PDF uploads.

Closes #67
```

## Architecture Guidelines

### Microservices

- Each service should have a single responsibility
- Services communicate via HTTP (no direct database access)
- Shared models go in service-specific schemas

### Repository Pattern

- Keep data access in `repositories/`
- Business logic in `domain/`
- Route handlers in `api/` should be thin

### Async/Await

- Use `async`/`await` consistently
- Don't mix sync and async database calls
- Use `asyncio.gather()` for parallel operations

## Project Structure

```
raas/
├── services/
│   ├── api/              # FastAPI gateway
│   │   ├── app/
│   │   │   ├── api/      # Route handlers
│   │   │   ├── domain/   # Business logic
│   │   │   ├── models/   # Database models
│   │   │   └── repositories/  # Data access
│   │   └── tests/
│   ├── embedder/         # Vector generation
│   ├── generator/        # LLM summaries
│   ├── search/           # Hybrid search
│   └── frontend/         # React UI
└── infrastructure/
    ├── docker-compose/   # Local dev
    └── k8s/              # Production deployment
```

## Getting Help

- Check existing [issues](../../issues)
- Read the [README](README.md)
- Review [architecture documentation](infrastructure/k8s/README.md)
- Ask questions in issue comments

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes (if applicable)
- Acknowledgments section

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and different perspectives
- Focus on constructive feedback
- Assume good intentions

### Not Acceptable

- Harassment or discriminatory language
- Personal attacks
- Trolling or inflammatory comments
- Publishing private information

---

## Thank You!

Your contributions help make this project better for everyone learning about RAG systems, microservices architecture, and cloud-native development.

Whether you're fixing a typo or implementing a new feature, every contribution is valuable.
