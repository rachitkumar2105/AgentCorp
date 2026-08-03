import React, { ReactNode } from 'react';
import { useAuth } from '../hooks/use-auth';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, fallback = null }) => {
  const { authenticated, loading } = useAuth();

  if (loading) {
    return (
      <main className="loading-screen" aria-live="polite">
        <div className="loading-card">
          <div className="loading-brand">AgentCorp</div>
          <p className="loading-motto">Enterprise AI Operating System</p>
          <div className="progress-track" aria-hidden="true">
            <div className="progress-bar" />
          </div>
        </div>
      </main>
    );
  }

  if (!authenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
