import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getRuntimeStatus, getRuntimeObservatory, getRuntimeArchitecture } from '../api/runtime';

export function useRuntime() {
  const statusQuery = useQuery({
    queryKey: queryKeys.runtime.status(),
    queryFn: getRuntimeStatus,
  });

  const observatoryQuery = useQuery({
    queryKey: queryKeys.runtime.observatory(),
    queryFn: getRuntimeObservatory,
  });

  const architectureQuery = useQuery({
    queryKey: queryKeys.runtime.architecture(),
    queryFn: getRuntimeArchitecture,
  });

  return {
    status: statusQuery.data ?? null,
    observatory: observatoryQuery.data ?? null,
    architecture: architectureQuery.data ?? null,
    isLoading: statusQuery.isLoading || observatoryQuery.isLoading || architectureQuery.isLoading,
    error: statusQuery.error || observatoryQuery.error || architectureQuery.error,
  };
}
