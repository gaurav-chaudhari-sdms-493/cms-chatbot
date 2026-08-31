export interface DetectedValue {
  id: number | string;
  label: string;
  confidence?: number;
}

export interface PlaceholderMetadata {
  placeholder_name: string;
  data_type: 'REFERENCE' | 'ENUM' | 'INTEGER' | 'DECIMAL' | 'DATE' | 'DATE_RANGE' | 'BOOLEAN';
  input_mode: string;
  source_table?: string;
  source_id_column?: string;
  source_label_column?: string;
  required: boolean;
  display_order?: number;
}

export interface TemplateSuggestion {
  template_id: string;
  intent: string;
  question_template: string;
  score: number;
  detected_values: Record<string, DetectedValue>;
  missing_placeholders: PlaceholderMetadata[];
}

export interface SuggestResponse {
  query: string;
  suggestions: TemplateSuggestion[];
}

export interface QueryExecutionResult {
  status: 'SUCCESS' | 'ERROR';
  template_id: string;
  execution_time_ms: number;
  total_rows: number;
  columns: string[];
  data: Record<string, any>[];
  error?: string;
}

export interface AdminQueryTemplate {
  template_id: string;
  intent: string;
  question_template: string;
  retrieval_text: string;
  sql_template: string;
  result_type: string;
  is_active: boolean;
  version: number;
  has_embedding: boolean;
  placeholders: PlaceholderMetadata[];
}

export interface AdminQueryTemplatePayload {
  template_id: string;
  intent: string;
  question_template: string;
  retrieval_text: string;
  sql_template: string;
  result_type: string;
  is_active: boolean;
  version: number;
  placeholders: PlaceholderMetadata[];
}

export interface CandidateTemplateDetail {
  template_id: string;
  intent: string;
  question_template: string;
  score: number;
}

export interface AgentQueryResponse {
  question: string;
  markdown_report: string;
  sql_used: string;
  template_id?: string | null;
  candidate_templates?: CandidateTemplateDetail[] | null;
  execution_time_ms: number;
  retry_count: number;
  status: string;
}

export interface ChatMessageResponse {
  id: number;
  session_id: string;
  sender: 'user' | 'agent';
  content: string;
  sql_used?: string | null;
  template_id?: string | null;
  candidate_templates?: CandidateTemplateDetail[] | null;
  execution_time_ms?: number | null;
  created_at: string;
}

export interface ChatSessionDetailResponse {
  id: string;
  title: string;
  mode: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessageResponse[];
}


