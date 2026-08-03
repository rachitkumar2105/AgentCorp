export interface Goal {
  id: number;
  title: string;
  description?: string;
  objective: string;
  priority: string;
  status: string;
  success_criteria?: string;
  organization_id: number;
  agent_id: number;
  conversation_id?: number | null;
  created_by?: number;
  created_at?: string;
  updated_at?: string;
}

export interface GoalCreate {
  title: string;
  description?: string;
  objective: string;
  priority: string;
  success_criteria?: string;
  agent_id: number;
  conversation_id?: number | null;
}
