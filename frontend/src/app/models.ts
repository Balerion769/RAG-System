export interface EvidenceItem {
  chunk_id: string;
  document_id: string;
  source_type: string;
  section: string | null;
  score: number;
  text: string;
  metadata: Record<string, unknown>;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  source_type: string;
  chunk_count: number;
  parent_count: number;
  extracted_characters: number;
  metadata: Record<string, unknown>;
}

export interface StartInterviewResponse {
  session_id: string;
  question: string;
  evidence: EvidenceItem[];
}

export interface AnswerResponse {
  session_id: string;
  feedback: string;
  scores: Record<string, number>;
  next_question: string;
  evidence: EvidenceItem[];
}

export interface ReportResponse {
  session_id: string;
  role_title: string;
  status: string;
  turns: InterviewTurn[];
  overall_scores: Record<string, number>;
  improvement_plan: string[];
  created_at: string;
}

export interface InterviewTurn {
  question: string;
  answer: string;
  feedback: string;
  scores: Record<string, number>;
  evidence: EvidenceItem[];
  created_at: string;
}

export interface VideoUploadResponse {
  session_id: string;
  filename: string;
  saved_path: string;
  metrics: Record<string, unknown>;
}

