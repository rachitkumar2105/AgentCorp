import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getGoals, getGoal, createGoal, executeGoal } from '../api/goals';
import type { GoalCreate } from '../types/goal';

export function useGoals(organizationId: number) {
  const query = useQuery({
    queryKey: queryKeys.goals.list(organizationId),
    queryFn: () => getGoals(organizationId),
    enabled: Boolean(organizationId),
  });

  return {
    goals: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useGoal(goalId: number, organizationId: number) {
  const query = useQuery({
    queryKey: queryKeys.goals.detail(goalId, organizationId),
    queryFn: () => getGoal(goalId, organizationId),
    enabled: Boolean(goalId) && Boolean(organizationId),
  });

  return {
    goal: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useCreateGoal(organizationId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GoalCreate) => createGoal(payload, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.goals.list(organizationId) });
    },
  });
}

export function useExecuteGoal(organizationId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goalId: number) => executeGoal(goalId, organizationId),
    onSuccess: (data, goalId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.goals.detail(goalId, organizationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.observability.diagnostics() });
    },
  });
}
