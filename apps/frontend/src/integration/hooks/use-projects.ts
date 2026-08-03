import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getProjects, getProject } from '../api/projects';

export function useProjects() {
  const query = useQuery({
    queryKey: queryKeys.projects.list(),
    queryFn: getProjects,
  });

  return {
    projects: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useProject(projectId: number) {
  const query = useQuery({
    queryKey: queryKeys.projects.detail(projectId),
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });

  return {
    project: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}
