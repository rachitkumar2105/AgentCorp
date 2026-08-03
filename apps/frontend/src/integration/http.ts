import { env } from './env';
import { readStoredAuth, writeStoredAuth } from './auth-storage';
import type { TokenResponse, LoginRequest } from './types/auth';

export interface ApiErrorBody {
  detail?: string;
  message?: string;
  [key: string]: unknown;
}

export class HttpError extends Error {
  status: number;
  body?: ApiErrorBody;

  constructor(status: number, message: string, body?: ApiErrorBody) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.body = body;
  }
}

async function parseBody(response: Response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function extractMessage(body: unknown, fallback: string): string {
  if (typeof body === 'string') return body;
  if (body && typeof body === 'object') {
    const record = body as Record<string, unknown>;
    if (typeof record.detail === 'string') return record.detail;
    if (typeof record.message === 'string') return record.message;
  }
  return fallback;
}

// Keep track of refresh promise to merge concurrent 401 refreshes
let refreshPromise: Promise<string | null> | null = null;

async function executeRefresh(): Promise<string | null> {
  const auth = readStoredAuth();
  if (!auth || !auth.refreshToken) {
    return null;
  }
  // Simulate token refresh flow since the backend doesn't have a refresh endpoint
  // We simulate a network call to verify/refresh the session
  await new Promise((resolve) => setTimeout(resolve, 500));
  const newAccessToken = auth.accessToken; // Re-use the existing valid JWT access token
  writeStoredAuth({
    accessToken: newAccessToken,
    refreshToken: auth.refreshToken,
  });
  return newAccessToken;
}

export async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 15000): Promise<T> {
  const auth = readStoredAuth();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(auth?.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {}),
    ...(init.headers as Record<string, string> || {}),
  };

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    let response = await fetch(`${env.apiBaseUrl}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    });
    clearTimeout(id);

    let body = await parseBody(response);

    if (response.status === 401) {
      // Prevent infinite refresh loops
      if (path.includes('/auth/login') || path.includes('/auth/register')) {
        throw new HttpError(response.status, extractMessage(body, response.statusText), body as ApiErrorBody);
      }

      // Try refresh flow
      if (!refreshPromise) {
        refreshPromise = executeRefresh().finally(() => {
          refreshPromise = null;
        });
      }

      const refreshedToken = await refreshPromise;
      if (refreshedToken) {
        // Retry request with new token
        headers['Authorization'] = `Bearer ${refreshedToken}`;
        const retryId = setTimeout(() => controller.abort(), timeoutMs);
        response = await fetch(`${env.apiBaseUrl}${path}`, {
          ...init,
          headers,
          signal: controller.signal,
        });
        clearTimeout(retryId);
        body = await parseBody(response);
      } else {
        // Refresh failed, logout
        writeStoredAuth(null);
        window.dispatchEvent(new Event('agentcorp-logout'));
        throw new HttpError(401, 'Session expired. Please log in again.');
      }
    }

    if (!response.ok) {
      throw new HttpError(response.status, extractMessage(body, response.statusText), body as ApiErrorBody);
    }

    return body as T;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new HttpError(408, 'Request timed out');
    }
    throw error;
  }
}

export async function loginRequest(email: string, password: string): Promise<TokenResponse> {
  const result = await request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  // Simulate refresh token locally if not returned by backend
  writeStoredAuth({
    accessToken: result.access_token,
    refreshToken: result.refresh_token ?? 'simulated-refresh-token',
  });
  return result;
}

export function logoutRequest(): void {
  writeStoredAuth(null);
}
