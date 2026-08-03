import { request } from '../http';
import type { ChatResponse, Conversation, ChatCreateRequest, ChatContinueRequest } from '../types/chat';

export async function createChat(payload: ChatCreateRequest, organizationId: number): Promise<ChatResponse> {
  return request<ChatResponse>(`/api/v1/chat?organization_id=${organizationId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function continueChat(conversationId: number, payload: ChatContinueRequest, organizationId: number): Promise<ChatResponse> {
  return request<ChatResponse>(`/api/v1/chat/${conversationId}?organization_id=${organizationId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getConversation(conversationId: number, organizationId: number): Promise<Conversation> {
  return request<Conversation>(`/api/v1/chat/${conversationId}?organization_id=${organizationId}`);
}
