import { request } from '../http';

export interface HealthStatus {
  status: string;
  timestamp: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/health');
}

export async function checkLiveness(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/live');
}

export async function checkReadiness(): Promise<HealthStatus> {
  return request<HealthStatus>('/health/ready');
}

export async function checkDependencies(): Promise<any> {
  return request<any>('/health/dependencies');
}
