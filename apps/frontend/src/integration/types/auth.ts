export interface TokenResponse {
  access_token: string;
  refresh_token?: string | null;
  token_type?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthSession {
  accessToken: string;
  refreshToken?: string | null;
}
