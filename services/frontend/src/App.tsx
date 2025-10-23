import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainPage } from './pages/MainPage';
import { DocumentDetailPage } from './pages/DocumentDetailPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/documents/:id" element={<DocumentDetailPage />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
