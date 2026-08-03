import { request } from '../http';
import type { Knowledge, KnowledgeDocument } from '../types/knowledge';

export async function createKnowledgeBase(payload: { name: string; description?: string; visibility: string }, organizationId: number): Promise<Knowledge> {
  return request<Knowledge>(`/api/v1/knowledge?organization_id=${organizationId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getKnowledgeBases(organizationId: number): Promise<Knowledge[]> {
  // Return empty list because there is no endpoint on backend to list knowledge bases
  return [];
}

export async function uploadDocument(knowledgeBaseId: number, organizationId: number, file: File, duplicatePolicy = 'reject'): Promise<KnowledgeDocument> {
  const formData = new FormData();
  formData.append('file', file);

  // We need to use custom request or fetch for FormData since request defaults to JSON
  // Let's pass undefined headers or override content-type to allow browser to set boundary
  const auth = (await import('../auth-storage')).readStoredAuth();
  const apiBaseUrl = (await import('../env')).env.apiBaseUrl;

  const response = await fetch(`${apiBaseUrl}/api/v1/knowledge/${knowledgeBaseId}/documents?organization_id=${organizationId}&duplicate_policy=${duplicatePolicy}`, {
    method: 'POST',
    headers: {
      ...(auth?.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    let detail = response.statusText;
    try {
      const parsed = JSON.parse(text);
      detail = parsed.detail || parsed.message || detail;
    } catch (e) {}
    throw new Error(detail);
  }

  return response.json() as Promise<KnowledgeDocument>;
}

export async function listDocuments(knowledgeBaseId: number, organizationId: number): Promise<KnowledgeDocument[]> {
  return request<KnowledgeDocument[]>(`/api/v1/knowledge/${knowledgeBaseId}/documents?organization_id=${organizationId}`);
}

export async function getDocument(documentId: number, organizationId: number): Promise<KnowledgeDocument> {
  return request<KnowledgeDocument>(`/api/v1/documents/${documentId}?organization_id=${organizationId}`);
}

export async function deleteDocument(documentId: number, organizationId: number): Promise<void> {
  return request<void>(`/api/v1/documents/${documentId}?organization_id=${organizationId}`, {
    method: 'DELETE',
  });
}
