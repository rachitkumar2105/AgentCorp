export interface Memory {
  id: number;
  title: string;
  content: string;
  memory_type: string;
  importance_score: number;
  confidence_score: number;
  organization_id: number;
  agent_id: number;
  conversation_id?: number | null;
  source: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  archived: boolean;
}

export interface MemoryCreate {
  title: string;
  content: string;
  memory_type?: string;
  importance_score?: number;
  confidence_score?: number;
  agent_id: number;
}
