export interface Knowledge {
  id: number;
  name: string;
  description?: string | null;
  visibility: string;
  organization_id: number;
  status: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocument {
  id: number;
  knowledge_base_id: number;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  checksum: string;
  language?: string | null;
  status: string;
  processing_status: string;
  page_count?: number | null;
  metadata_json?: Record<string, any> | null;
  uploaded_by: number;
  created_at: string;
  updated_at: string;
}
