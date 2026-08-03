import { request } from '../http';
import type { MetricsSnapshot, DiagnosticsResponse, AuditLog } from '../types/observability';

export async function getSystemMetrics(): Promise<MetricsSnapshot> {
  return request<MetricsSnapshot>('/api/v1/operations/metrics');
}

export async function getDiagnostics(): Promise<DiagnosticsResponse> {
  return request<DiagnosticsResponse>('/api/v1/operations/executions');
}

export async function getAuditLogs(skip = 0, limit = 100, organizationId?: number): Promise<AuditLog[]> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (organizationId !== undefined) {
    params.append('organization_id', String(organizationId));
  }
  return request<AuditLog[]>(`/api/v1/audit?${params.toString()}`);
}
