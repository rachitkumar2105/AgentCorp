import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <main className="loading-screen" style={{ background: 'var(--bg-primary, #09090b)' }}>
          <div className="loading-card" style={{ maxWidth: '500px', textAlign: 'center' }}>
            <div className="loading-brand" style={{ color: 'var(--red, #ef4444)' }}>System Error</div>
            <p className="loading-motto">Something went wrong inside the platform</p>
            <pre style={{
              background: 'var(--bg-secondary, #18181b)',
              color: 'var(--text-secondary, #a1a1aa)',
              padding: '1rem',
              borderRadius: '6px',
              fontSize: '0.85rem',
              textAlign: 'left',
              overflowX: 'auto',
              border: '1px solid var(--border, #27272a)'
            }}>
              {this.state.error?.message || 'Unknown runtime error'}
            </pre>
            <button
              className="primary"
              style={{ marginTop: '1.5rem', width: '100%' }}
              onClick={() => window.location.reload()}
            >
              Reload Application
            </button>
          </div>
        </main>
      );
    }

    return this.props.children;
  }
}
