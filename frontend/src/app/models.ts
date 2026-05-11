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
  verification: VerificationResponse | null;
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
  verification: VerificationResponse | null;
  created_at: string;
}

export interface VideoUploadResponse {
  session_id: string;
  filename: string;
  saved_path: string;
  metrics: Record<string, unknown>;
}

export interface WebSourceItem {
  title: string;
  url: string;
  snippet: string;
  provider: string;
  fetched_text: string;
  score: number;
}

export interface ClaimCheckItem {
  claim: string;
  verdict: string;
  confidence: number;
  explanation: string;
  sources: WebSourceItem[];
}

export interface VerificationResponse {
  enabled: boolean;
  provider: string;
  overall_verdict: string;
  overall_score: number;
  summary: string;
  corrected_answer: string;
  claims: ClaimCheckItem[];
  sources: WebSourceItem[];
  limitations: string[];
}
