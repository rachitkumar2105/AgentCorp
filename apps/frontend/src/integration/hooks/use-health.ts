import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { checkHealth, checkLiveness, checkReadiness, checkDependencies } from '../api/health';

export function useHealth() {
  const healthQuery = useQuery({
    queryKey: queryKeys.health.all(),
    queryFn: checkHealth,
  });

  const liveQuery = useQuery({
    queryKey: queryKeys.health.live(),
    queryFn: checkLiveness,
  });

  const readyQuery = useQuery({
    queryKey: queryKeys.health.ready(),
    queryFn: checkReadiness,
  });

  const dependenciesQuery = useQuery({
    queryKey: queryKeys.health.dependencies(),
    queryFn: checkDependencies,
  });

  return {
    health: healthQuery.data,
    isHealthy: healthQuery.data?.status === 'healthy',
    isLoading: healthQuery.isLoading || liveQuery.isLoading || readyQuery.isLoading,
    live: liveQuery.data,
    ready: readyQuery.data,
    dependencies: dependenciesQuery.data,
  };
}
