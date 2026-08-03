import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { readStoredAuth, writeStoredAuth } from '../auth-storage';
import { getProfile, login as apiLogin, logout as apiLogout } from '../api/auth';
import type { User } from '../types/user';
import type { LoginRequest } from '../types/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  organization: string | null;
  permissions: string[];
  loading: boolean;
  authenticated: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUserProfile = async () => {
    try {
      const profile = await getProfile();
      setUser(profile);
    } catch (e) {
      // Failed to retrieve profile, clear token
      writeStoredAuth(null);
      setToken(null);
      setUser(null);
    }
  };

  const rehydrate = async () => {
    setLoading(true);
    const stored = readStoredAuth();
    if (stored?.accessToken) {
      setToken(stored.accessToken);
      try {
        await fetchUserProfile();
      } catch (e) {
        // Suppress profile fetch errors during rehydration to avoid crash
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    rehydrate();

    // Listen for custom logout events dispatched by the http client on 401 expiration
    const handleLogoutEvent = () => {
      setToken(null);
      setUser(null);
    };
    window.addEventListener('agentcorp-logout', handleLogoutEvent);
    return () => {
      window.removeEventListener('agentcorp-logout', handleLogoutEvent);
    };
  }, []);

  const login = async (payload: LoginRequest) => {
    setLoading(true);
    try {
      const response = await apiLogin(payload);
      setToken(response.access_token);
      // Wait for profile fetch
      const profile = await getProfile();
      setUser(profile);
    } catch (error) {
      setToken(null);
      setUser(null);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    apiLogout();
    setToken(null);
    setUser(null);
  };

  const refresh = async () => {
    // Simulated token refresh
    const stored = readStoredAuth();
    if (stored?.refreshToken) {
      // Rehydrate/refresh session
      await rehydrate();
    }
  };

  const organization = user?.organization_id ? String(user.organization_id) : null;
  const permissions = user?.permissions || [];
  const authenticated = Boolean(token);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        organization,
        permissions,
        loading,
        authenticated,
        login,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
