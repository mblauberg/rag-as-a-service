# Frontend Specification (Phase 2)

This document summarises the requirements for the React‑based frontend of RAAS. It explains the technologies to use, the structure of the application, and the user interface features.  Claude Code should rely on this file when scaffolding the frontend and integrating API calls.

## Overview

The frontend is built with React 18 and TypeScript, bundled using Vite. Tailwind CSS provides utility‑first styling, React Router manages navigation, Axios is used for API calls, and React Query handles client‑side state and caching.  The application runs inside a Docker container served by NGINX.

## Features

The application should provide the following core features:

- **Home page**: landing page with a form to upload documents.  Includes a progress indicator during file upload.
- **Documents page**: lists all uploaded documents with pagination.  Each entry displays the title, file name, creation date and chunk count.  Includes a delete button with confirmation.
- **Document detail page**: shows a single document, listing each chunk with its index and text.
- **Search page**: allows users to perform semantic search.  Displays results with document title, chunk text and similarity score.  Highlights search terms if possible.
- **Responsive design**: the UI should be usable on both desktop and mobile devices.
- **Error and loading states**: indicate when data is being fetched or if an error occurs.

## Directory structure

Use the following layout for React code:

```
services/frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Spinner.tsx
│   │   ├── documents/
│   │   │   ├── DocumentCard.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   └── UploadForm.tsx
│   │   ├── search/
│   │   │   ├── SearchBar.tsx
│   │   │   └── SearchResults.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Footer.tsx
│   │       └── Layout.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── SearchPage.tsx
│   │   └── DocumentDetailPage.tsx
│   ├── services/
│   │   └── api.ts           # API client encapsulating Axios requests
│   ├── hooks/
│   │   ├── useDocuments.ts   # React Query hooks for documents
│   │   └── useSearch.ts      # React Query hooks for search
│   ├── types/
│   │   └── index.ts          # Shared TypeScript types
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css             # Tailwind imports
├── Dockerfile                # Build using multi‑stage Node/NGINX container
├── nginx.conf                # NGINX configuration for routing
├── package.json              # npm/TypeScript dependencies
├── tsconfig.json             # TypeScript configuration
├── vite.config.ts            # Vite build settings
└── tailwind.config.js        # Tailwind customisation
```

## API integration

Encapsulate all HTTP requests in a dedicated API client (`src/services/api.ts`).  Use Axios to make requests to the FastAPI gateway at the base URL defined by `VITE_API_URL`.  Expose methods for uploading documents, listing documents, retrieving individual documents, deleting documents, performing search queries, and checking health.

React Query should cache responses and provide automatic refetching.  Create custom hooks (`useDocuments`, `useSearch`) to wrap API calls and handle loading and error states.

## Styling and accessibility

Adopt Tailwind CSS for styling components.  Use semantic HTML elements where possible, ensuring buttons, forms and interactive elements are accessible.  Include ARIA labels when necessary.  Keep the design consistent with a modern minimal look.

This document provides the front‑end context for Claude Code.  For detailed API schemas and endpoints, refer to `api_service.md`.