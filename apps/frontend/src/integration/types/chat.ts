export interface Usage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface AssistantMessage {
  id: number;
  role: 'assistant';
  content: string;
  provider?: string | null;
  model_used?: string | null;
  finish_reason?: string | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  total_tokens?: number | null;
  created_at: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  provider?: string | null;
  model_used?: string | null;
  finish_reason?: string | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  total_tokens?: number | null;
  created_at: string;
}

export interface ChatResponse {
  conversation_id: number;
  runtime_version?: string | null;
  assistant_message: AssistantMessage;
  provider: string;
  model: string;
  usage: Usage;
  finish_reason: string;
  created_at: string;
}

export interface Conversation {
  conversation_id: number;
  title?: string | null;
  runtime_version?: string | null;
  agent_id: number;
  organization_id: number;
  user_id: number;
  messages: Message[];
  page: number;
  page_size: number;
  total_messages: number;
  created_at: string;
  updated_at: string;
}

export interface ChatCreateRequest {
  message: string;
  agent_id: number;
  provider?: string;
  model?: string;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  runtime_version?: string;
  stream?: boolean;
}

export interface ChatContinueRequest {
  message: string;
  provider?: string;
  model?: string;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  runtime_version?: string;
  stream?: boolean;
}
