const tokenKey = 'agentcorp.auth';

export interface StoredAuth {
  accessToken: string;
  refreshToken?: string | null;
}

export function readStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(tokenKey);
    if (!raw) return null;
    return JSON.parse(raw) as StoredAuth;
  } catch {
    return null;
  }
}

export function writeStoredAuth(auth: StoredAuth | null) {
  if (!auth) {
    localStorage.removeItem(tokenKey);
    return;
  }
  localStorage.setItem(tokenKey, JSON.stringify(auth));
}
