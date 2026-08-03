import { queryKeys } from './query-keys';
import * as api from '../api';

export const queryOptions = {
  auth: {
    profile: () => ({
      queryKey: queryKeys.auth.profile(),
      queryFn: () => api.auth.getProfile(),
    }),
  },
  health: {
    check: () => ({
      queryKey: queryKeys.health.all(),
      queryFn: () => api.health.checkHealth(),
    }),
  },
  projects: {
    list: () => ({
      queryKey: queryKeys.projects.list(),
      queryFn: () => api.projects.getProjects(),
    }),
    detail: (id: number) => ({
      queryKey: queryKeys.projects.detail(id),
      queryFn: () => api.projects.getProject(id),
    }),
  },
  goals: {
    list: (orgId: number) => ({
      queryKey: queryKeys.goals.list(orgId),
      queryFn: () => api.goals.getGoals(orgId),
    }),
    detail: (id: number, orgId: number) => ({
      queryKey: queryKeys.goals.detail(id, orgId),
      queryFn: () => api.goals.getGoal(id, orgId),
    }),
  },
  tasks: {
    list: () => ({
      queryKey: queryKeys.tasks.list(),
      queryFn: () => api.tasks.getTasks(),
    }),
  },
  chat: {
    detail: (id: number, orgId: number) => ({
      queryKey: queryKeys.chat.detail(id, orgId),
      queryFn: () => api.chat.getConversation(id, orgId),
    }),
  },
  workflows: {
    list: (orgId: number) => ({
      queryKey: queryKeys.workflows.list(orgId),
      queryFn: () => api.workflows.createWorkflow, // placeholder mapping, or custom fetchers
    }),
  },
  knowledge: {
    list: (orgId: number) => ({
      queryKey: queryKeys.knowledge.list(orgId),
      queryFn: () => api.knowledge.getKnowledgeBases(orgId),
    }),
  },
  memory: {
    list: (orgId: number, agentId?: number, type?: string) => ({
      queryKey: queryKeys.memory.list(orgId, agentId, type),
      queryFn: () => api.memory.getMemories(orgId, agentId, type),
    }),
  },
  runtime: {
    status: () => ({
      queryKey: queryKeys.runtime.status(),
      queryFn: () => api.runtime.getRuntimeStatus(),
    }),
  },
  observability: {
    metrics: () => ({
      queryKey: queryKeys.observability.metrics(),
      queryFn: () => api.observability.getSystemMetrics(),
    }),
    diagnostics: () => ({
      queryKey: queryKeys.observability.diagnostics(),
      queryFn: () => api.observability.getDiagnostics(),
    }),
  },
};
