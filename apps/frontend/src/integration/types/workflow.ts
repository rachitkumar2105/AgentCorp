export interface Node {
  id?: number;
  name: string;
  node_type: string;
  configuration?: Record<string, any>;
  timeout: number;
}

export interface Edge {
  id?: number;
  source_node_id: number;
  target_node_id: number;
  transition_condition?: string | null;
  priority: number;
}

export interface Workflow {
  id: number;
  name: string;
  description?: string | null;
  version: string;
  organization_id: number;
  status: string;
  enabled: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  version: string;
  nodes: Node[];
  edges: Edge[];
}

export interface WorkflowExecution {
  id: number;
  workflow_id: number;
  status: string;
  current_node_id?: number | null;
  started_at: string;
  completed_at?: string | null;
  duration?: number | null;
  execution_context: Record<string, any>;
}
