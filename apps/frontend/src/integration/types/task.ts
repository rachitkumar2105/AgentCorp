export interface Task {
  id: number;
  goal_id: number;
  parent_task_id?: number | null;
  title: string;
  description?: string;
  status: string;
  priority: string;
  order: number;
  estimated_cost: number;
  estimated_tokens: number;
  execution_type: string;
  retry_count: number;
  created_at?: string;
  updated_at?: string;
}
