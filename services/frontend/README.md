# RAAS Frontend

React-based frontend for RAAS (Retrieval-Augmented Generation as a Service).

## Features

- Document upload with progress tracking
- Document listing with pagination
- Document detail view with chunks
- Semantic search with results highlighting
- Responsive design with Tailwind CSS
- React Query for state management

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios
- TanStack React Query

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

# Lint
npm run lint
```

The app will be available at http://localhost:3000

## Docker

### Build

```bash
docker build -t raas-frontend .
```

### Run

```bash
docker run -p 3000:3000 raas-frontend
```

## Project Structure

```
src/
├── components/
│   ├── common/          # Reusable UI components
│   ├── documents/       # Document-related components
│   ├── search/          # Search components
│   └── layout/          # Layout components
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
