import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getMemories, getMemory, createMemory, updateMemory } from '../api/memory';
import type { MemoryCreate } from '../types/memory';

export function useMemory(organizationId: number, agentId?: number, memoryType?: string) {
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: queryKeys.memory.list(organizationId, agentId, memoryType),
    queryFn: () => getMemories(organizationId, agentId, memoryType),
    enabled: Boolean(organizationId),
  });

  const createMutation = useMutation({
    mutationFn: (payload: MemoryCreate) => createMemory(payload, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.memory.list(organizationId, agentId, memoryType) });
    },
  });

  return {
    memories: listQuery.data ?? [],
    isLoadingMemories: listQuery.isLoading,
    createMemory: (payload: MemoryCreate) => createMutation.mutateAsync(payload),
    isCreating: createMutation.isPending,
  };
}

export function useMemoryDetail(memoryId: number, organizationId: number) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.memory.detail(memoryId, organizationId),
    queryFn: () => getMemory(memoryId, organizationId),
    enabled: Boolean(memoryId) && Boolean(organizationId),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<MemoryCreate>) => updateMemory(memoryId, payload, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.memory.detail(memoryId, organizationId) });
      queryClient.invalidateQueries({ queryKey: ['memory'] });
    },
  });

  return {
    memory: query.data ?? null,
    isLoading: query.isLoading,
    updateMemory: (payload: Partial<MemoryCreate>) => updateMutation.mutateAsync(payload),
    isUpdating: updateMutation.isPending,
  };
}
