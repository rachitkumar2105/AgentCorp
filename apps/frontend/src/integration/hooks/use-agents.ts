import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getAgents, getAgent } from '../api/agents';

export function useAgents() {
  const query = useQuery({
    queryKey: queryKeys.agents.list(),
    queryFn: getAgents,
  });

  return {
    agents: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useAgent(agentId: number) {
  const query = useQuery({
    queryKey: queryKeys.agents.detail(agentId),
    queryFn: () => getAgent(agentId),
    enabled: Boolean(agentId),
  });

  return {
    agent: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}
