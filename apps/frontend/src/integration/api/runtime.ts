import { request } from '../http';
import type { Runtime } from '../types/runtime';

export async function getRuntimeStatus(): Promise<Runtime> {
  // Let's retrieve observatory data or default to generic status
  try {
    const observatory = await request<any>('/api/v1/runtime/observatory');
    return {
      version: observatory?.version || 'V2',
      status: observatory?.status || 'running',
      configured_providers: observatory?.configured_providers || [],
      uptime: observatory?.uptime || 0,
    };
  } catch (error) {
    // Fallback to static info
    return {
      version: 'V2',
      status: 'unknown',
    };
  }
}

export async function getRuntimeObservatory(): Promise<any> {
  return request<any>('/api/v1/runtime/observatory');
}

export async function getRuntimeArchitecture(): Promise<any> {
  return request<any>('/api/v1/runtime/architecture');
}
