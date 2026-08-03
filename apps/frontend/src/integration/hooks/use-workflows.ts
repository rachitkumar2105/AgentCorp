import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { createWorkflow, executeWorkflow, getWorkflowExecution } from '../api/workflows';
import type { WorkflowCreate } from '../types/workflow';

export function useWorkflow(workflowId: number, organizationId: number) {
  const queryClient = useQueryClient();

  const execute = useMutation({
    mutationFn: (agentId: number) => executeWorkflow(workflowId, organizationId, agentId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.execution(data.id, organizationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.observability.diagnostics() });
    },
  });

  return {
    executeMutation: execute,
    executeWorkflow: (agentId: number) => execute.mutateAsync(agentId),
    isExecuting: execute.isPending,
  };
}

export function useCreateWorkflow(organizationId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: WorkflowCreate) => createWorkflow(payload, organizationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.list(organizationId) });
    },
  });
}

export function useWorkflowExecution(executionId: number, organizationId: number) {
  const query = useQuery({
    queryKey: queryKeys.workflows.execution(executionId, organizationId),
    queryFn: () => getWorkflowExecution(executionId, organizationId),
    enabled: Boolean(executionId) && Boolean(organizationId),
  });

  return {
    execution: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}
