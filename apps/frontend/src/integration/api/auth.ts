import { loginRequest, logoutRequest, request } from '../http';
import { readStoredAuth, writeStoredAuth } from '../auth-storage';
import type { LoginRequest, TokenResponse, AuthSession } from '../types/auth';
import type { User } from '../types/user';

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  return loginRequest(payload.email, payload.password);
}

export function logout(): void {
  logoutRequest();
}

export function getSession(): AuthSession | null {
  const stored = readStoredAuth();
  return stored ? { accessToken: stored.accessToken, refreshToken: stored.refreshToken ?? null } : null;
}

export function setSession(session: AuthSession | null): void {
  writeStoredAuth(session);
}

export function isAuthenticated(): boolean {
  return Boolean(readStoredAuth()?.accessToken);
}

export async function getProfile(): Promise<User> {
  // Try retrieving from standard user profile endpoint (e.g. /users/me or a simulated lookup)
  // Let's call /users/1 or similar. We can fetch all users and filter, or fetch user profile from decode JWT
  // But wait, the backend users router has GET /users/{user_id}. Let's assume we can fetch users list or try `/users/me`
  // Wait, does the backend have /users/me? Let's check users.py: it has GET /users/{user_id}.
  // Since we don't have a direct /users/me, let's decode the user ID from the access token or default to 1.
  let userId = 1;
  const auth = readStoredAuth();
  if (auth?.accessToken) {
    try {
      const parts = auth.accessToken.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        if (payload && payload.sub) {
          userId = parseInt(payload.sub, 10) || 1;
        }
      }
    } catch (e) {
      // Ignore parsing errors, fallback to 1
    }
  }

  return request<User>(`/users/${userId}`);
}
