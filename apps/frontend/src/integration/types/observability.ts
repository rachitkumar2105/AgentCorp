export interface AuditLog {
  id: number;
  action: string;
  user_id: number;
  organization_id?: number | null;
  timestamp: string;
  metadata?: Record<string, any> | null;
}

export interface MetricsSnapshot {
  counters: Record<string, Record<string, number>>;
  gauges: Record<string, Record<string, number>>;
  histograms: Record<string, Array<Record<string, any>>>;
}

export interface DiagnosticsResponse {
  active_executions_count: number;
  active_executions: Array<Record<string, any>>;
  active_streams_count: number;
  active_streams: Array<Record<string, any>>;
  active_sessions_count: number;
  active_sessions: Array<Record<string, any>>;
  active_workflows_count: number;
  active_workflows: Array<Record<string, any>>;
}
