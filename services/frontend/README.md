# RAAS Frontend

React-based frontend for RAAS (Retrieval-Augmented Generation as a Service).

## Features

- **Document Management**: Upload with drag-and-drop, progress tracking, and file validation
- **Document Listing**: Paginated view with metadata display
- **Document Details**: View full document with chunks
- **Semantic Search**: Real-time search with relevance scoring
- **RAG Summaries**: AI-generated summaries with citations using multiple LLM providers
- **Model Selection**: Choose from OpenAI, Ollama, Anthropic, or Google models
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS
- **shadcn/ui Components**: Pre-built accessible components with Radix UI
- **State Management**: TanStack React Query for caching and optimistic updates

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Component library (Radix UI + Tailwind)
- **React Router** - SPA routing
- **Axios** - HTTP client
- **TanStack React Query** - Server state management
- **React Dropzone** - File upload
- **Framer Motion** - Animations
- **Lucide React** - Icon library
- **Vitest** - Unit testing
- **React Testing Library** - Component testing

## Development

### Prerequisites

- Node.js 18+
- npm

### Setup

```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Update VITE_API_URL if needed
# VITE_API_URL=http://localhost:8000
```

### Run

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

The app will be available at http://localhost:5173 (dev) or http://localhost:4173 (preview)

### Testing

```bash
# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Docker

### Build

```bash
docker build -t raas-frontend .
```

### Run

```bash
docker run -p 3000:3000 raas-frontend
```

The app will be available at http://localhost:3000

## Project Structure

```
src/
├── components/
│   ├── common/          # Reusable UI components
│   ├── documents/       # Document-related components
│   ├── search/          # Search components (SearchResults, SummaryDisplay, EnhancedSearchBar)
│   ├── upload/          # File upload components
│   ├── ui/              # shadcn/ui components (button, dialog, input, textarea)
│   └── ErrorBoundary.tsx # Global error boundary
├── pages/               # Page components
├── hooks/               # React Query hooks
├── services/            # API client
├── types/               # TypeScript types
├── App.tsx              # Main app with routing
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## API Integration

The frontend communicates with the FastAPI backend at `VITE_API_URL`. All API calls are centralized in `src/services/api.ts` and wrapped with React Query hooks for caching and state management.

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)
