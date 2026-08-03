import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../utils/query-keys';
import { getTasks, getTask } from '../api/tasks';

export function useTasks() {
  const query = useQuery({
    queryKey: queryKeys.tasks.list(),
    queryFn: getTasks,
  });

  return {
    tasks: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useTask(taskId: number) {
  const query = useQuery({
    queryKey: queryKeys.tasks.detail(taskId),
    queryFn: () => getTask(taskId),
    enabled: Boolean(taskId),
  });

  return {
    task: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}
