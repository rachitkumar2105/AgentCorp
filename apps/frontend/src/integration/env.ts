export const env = {
  apiBaseUrl: (import.meta as any).env.VITE_BACKEND_URL ?? 'http://localhost:8000',
  apiVersion: (import.meta as any).env.VITE_API_VERSION ?? 'v1',
  runtimeVersion: (import.meta as any).env.VITE_RUNTIME_VERSION ?? 'V2',
} as const;
