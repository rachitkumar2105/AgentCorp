export interface Agent {
  id: number;
  name: string;
  role: string;
  description?: string | null;
  status: string;
  organization_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface Execution {
  id: number;
  agent_id: number;
  status: string;
  started_at: string;
  completed_at?: string | null;
  duration?: number | null;
  execution_context: Record<string, any>;
}
