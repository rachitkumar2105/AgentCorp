import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';
import { App } from './ui/App';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './integration/query-client';
import { AuthProvider } from './integration/contexts/auth-context';
import { ErrorBoundary } from './integration/providers/error-boundary';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);

