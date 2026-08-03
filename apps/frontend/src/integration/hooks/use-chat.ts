import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getConversation, createChat, continueChat } from '../api/chat';
import type { ChatCreateRequest, ChatContinueRequest } from '../types/chat';

export function useConversation(conversationId: number, organizationId: number) {
  const query = useQuery({
    queryKey: queryKeys.chat.detail(conversationId, organizationId),
    queryFn: () => getConversation(conversationId, organizationId),
    enabled: Boolean(conversationId) && Boolean(organizationId),
  });

  return {
    conversation: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useCreateChat(organizationId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ChatCreateRequest) => createChat(payload, organizationId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.detail(data.conversation_id, organizationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.observability.diagnostics() });
    },
  });
}

export function useContinueChat(conversationId: number, organizationId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ChatContinueRequest) => continueChat(conversationId, payload, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.detail(conversationId, organizationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.observability.diagnostics() });
    },
  });
}
