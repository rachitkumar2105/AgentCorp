import { request } from '../http';
import type { Memory, MemoryCreate } from '../types/memory';

export async function createMemory(payload: MemoryCreate, organizationId: number): Promise<Memory> {
  return request<Memory>(`/api/v1/memory?organization_id=${organizationId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getMemories(organizationId: number, agentId?: number, memoryType?: string): Promise<Memory[]> {
  const params = new URLSearchParams({ organization_id: String(organizationId) });
  if (agentId !== undefined) params.append('agent_id', String(agentId));
  if (memoryType) params.append('memory_type', memoryType);

  return request<Memory[]>(`/api/v1/memory?${params.toString()}`);
}

export async function getMemory(memoryId: number, organizationId: number): Promise<Memory> {
  return request<Memory>(`/api/v1/memory/${memoryId}?organization_id=${organizationId}`);
}

export async function updateMemory(memoryId: number, payload: Partial<MemoryCreate>, organizationId: number): Promise<Memory> {
  return request<Memory>(`/api/v1/memory/${memoryId}?organization_id=${organizationId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}
