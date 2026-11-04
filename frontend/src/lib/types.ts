export type UserRole = "recruiter" | "client_hiring_manager";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  client_id?: number | null;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
  role?: UserRole;
  client_id?: number | null;
  user?: User;
}

export type PipelineStage =
  | "sourced"
  | "screened"
  | "submitted_to_client"
  | "client_reviewed"
  | "interview_scheduled"
  | "offer_made"
  | "joined";

export type ClientDecision = "shortlisted" | "rejected" | "interview_proposed";

export interface ScorecardCriterionItem {
  id?: string;
  name: string;
  type: string;
  weight: number; // 0.1 to 3.0
  required: boolean;
  value?: string | number | null;
}

export interface ScorecardData {
  skills?: string[];
  experience_min?: number | null;
  experience_max?: number | null;
  notice_days_max?: number | null;
  ctc_max?: number | null;
  location?: string | null;
  criteria?: ScorecardCriterionItem[];
  [key: string]: any;
}

export interface ClientItem {
  id: number;
  name: string;
  contact_email: string;
}

export interface Requisition {
  id: number;
  title: string;
  client_id: number;
  client_name?: string;
  jd_text: string;
  scorecard?: ScorecardData | null;
  status: string;
  created_at: string;
  candidates_count?: number;
}

export interface CandidateScoreEvidence {
  [criterion: string]: {
    score?: number;
    evidence_lines?: string[] | string;
    reasoning?: string;
  } | any;
}

export interface Candidate {
  id: number;
  name: string;
  email?: string | null;
  phone?: string | null;
  current_role?: string | null;
  experience_years?: number | null;
  notice_days?: number | null;
  skills?: string[] | null;
  ai_score?: number | null;
  score_evidence?: CandidateScoreEvidence | null;
  pipeline_stage?: PipelineStage | string | null;
  submitted_to_client?: boolean;
  viewed_by_recruiter?: boolean;
  client_decision?: ClientDecision | string | null;
  rejection_reason?: string | null;
  proposed_slot?: string | null;
}

export interface RankedItem {
  id?: number;
  submission_id?: number;
  submission?: {
    id: number;
    pipeline_stage: string;
    submitted_to_client: boolean;
    viewed_by_recruiter: boolean;
    client_decision?: string | null;
    rejection_reason?: string | null;
    proposed_slot?: string | null;
  };
  candidate: Candidate;
  criteria_scores?: Record<string, any>;
  ai_score?: number;
  score_evidence?: CandidateScoreEvidence;
}

export interface FileUploadItem {
  id: string;
  file: File;
  name: string;
  size: number;
  status: "queued" | "uploading" | "parsed" | "scored" | "duplicate" | "error";
  progress: number;
  error?: string;
  score?: number;
}

export interface PipelineSummary {
  [stage: string]: number;
}
