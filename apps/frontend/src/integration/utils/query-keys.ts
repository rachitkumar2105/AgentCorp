export const queryKeys = {
  auth: {
    profile: () => ['auth', 'profile'] as const,
    session: () => ['auth', 'session'] as const,
  },
  health: {
    all: () => ['health'] as const,
    live: () => ['health', 'live'] as const,
    ready: () => ['health', 'ready'] as const,
    dependencies: () => ['health', 'dependencies'] as const,
  },
  projects: {
    list: () => ['projects'] as const,
    detail: (id: number) => ['projects', id] as const,
  },
  goals: {
    list: (orgId: number) => ['goals', { orgId }] as const,
    detail: (id: number, orgId: number) => ['goals', id, { orgId }] as const,
  },
  tasks: {
    list: () => ['tasks'] as const,
    detail: (id: number) => ['tasks', id] as const,
  },
  chat: {
    detail: (id: number, orgId: number) => ['chat', id, { orgId }] as const,
  },
  workflows: {
    list: (orgId: number) => ['workflows', { orgId }] as const,
    detail: (id: number, orgId: number) => ['workflows', id, { orgId }] as const,
    execution: (id: number, orgId: number) => ['workflows', 'execution', id, { orgId }] as const,
  },
  agents: {
    list: () => ['agents'] as const,
    detail: (id: number) => ['agents', id] as const,
  },
  knowledge: {
    list: (orgId: number) => ['knowledge', { orgId }] as const,
    documents: (kbId: number, orgId: number) => ['knowledge', kbId, 'documents', { orgId }] as const,
    documentDetail: (id: number, orgId: number) => ['knowledge', 'document', id, { orgId }] as const,
  },
  memory: {
    list: (orgId: number, agentId?: number, type?: string) => ['memory', { orgId, agentId, type }] as const,
    detail: (id: number, orgId: number) => ['memory', id, { orgId }] as const,
  },
  runtime: {
    status: () => ['runtime', 'status'] as const,
    observatory: () => ['runtime', 'observatory'] as const,
    architecture: () => ['runtime', 'architecture'] as const,
  },
  observability: {
    metrics: () => ['observability', 'metrics'] as const,
    diagnostics: () => ['observability', 'diagnostics'] as const,
    auditLogs: (orgId?: number) => ['observability', 'audit', { orgId }] as const,
  },
};
