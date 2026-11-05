import axios from "axios";
import { getToken } from "./auth";
import {
  AuthResponse,
  Candidate,
  ClientDecision,
  ClientItem,
  PipelineStage,
  PipelineSummary,
  RankedItem,
  Requisition,
  ScorecardData,
  User,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export async function loginApi(credentials: { email: string; password: string }): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", credentials);
  return data;
}

export async function getMeApi(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}

// Clients
export async function getClientsApi(): Promise<ClientItem[]> {
  const { data } = await apiClient.get<ClientItem[]>("/clients");
  return data;
}

// Requisitions API
export async function getRequisitionsApi(): Promise<Requisition[]> {
  const { data } = await apiClient.get<Requisition[]>("/requisitions");
  return data;
}

export async function createRequisitionApi(payload: {
  title: string;
  client_id: string | number;
  jd_text: string;
}): Promise<Requisition> {
  const { data } = await apiClient.post<Requisition>("/requisitions", payload);
  return data;
}

export async function getRequisitionApi(id: number | string): Promise<Requisition> {
  const { data } = await apiClient.get<Requisition>(`/requisitions/${id}`);
  return data;
}

export async function updateScorecardApi(
  id: number | string,
  scorecard: ScorecardData | Record<string, any>
): Promise<Requisition> {
  const { data } = await apiClient.patch<Requisition>(`/requisitions/${id}/scorecard`, {
    scorecard,
  });
  return data;
}

// Upload Candidates API
export async function uploadCandidatesApi(
  requisitionId: number | string,
  files: File[],
  onProgress?: (progress: number) => void
): Promise<any> {
  const formData = new FormData();
  formData.append("requisition_id", String(requisitionId));
  files.forEach((file) => {
    formData.append("files", file);
  });

  const { data } = await apiClient.post("/candidates/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
  return data;
}

// Single candidate upload helper for per-file tracking if needed
export async function uploadSingleCandidateApi(
  requisitionId: number | string,
  file: File
): Promise<any> {
  const formData = new FormData();
  formData.append("requisition_id", String(requisitionId));
  formData.append("files", file);

  const { data } = await apiClient.post("/candidates/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

// Ranked Candidates API
export async function getRankedCandidatesApi(requisitionId: number | string): Promise<RankedItem[]> {
  const { data } = await apiClient.get<RankedItem[]>(`/requisitions/${requisitionId}/ranked`);
  return data;
}

// Pipeline API
export async function getPipelineSummaryApi(
  requisitionId: number | string
): Promise<PipelineSummary> {
  const { data } = await apiClient.get<PipelineSummary>(`/requisitions/${requisitionId}/pipeline`);
  return data;
}

export async function updateSubmissionStageApi(
  submissionId: string | number,
  stage: PipelineStage
): Promise<any> {
  const { data } = await apiClient.patch(`/submissions/${submissionId}/stage`, { stage });
  return data;
}

export async function submitToClientApi(submissionId: string | number): Promise<any> {
  const { data } = await apiClient.post(`/submissions/${submissionId}/submit-to-client`);
  return data;
}

export async function markCandidateViewedApi(candidateId: string | number): Promise<any> {
  try {
    const { data } = await apiClient.patch(`/candidates/${candidateId}/viewed`);
    return data;
  } catch {
    // If backend doesn't implement /candidates/{id}/viewed, handle gracefully
    return { success: true };
  }
}

// Client Portal API
export async function getClientRequisitionsApi(): Promise<Requisition[]> {
  const { data } = await apiClient.get<Requisition[]>("/client/requisitions");
  return data;
}

export async function getClientSubmissionsApi(
  requisitionId: number | string
): Promise<any[]> {
  const { data } = await apiClient.get<any[]>(
    `/client/requisitions/${requisitionId}/submissions`
  );
  return data;
}

export async function submitClientDecisionApi(
  submissionId: string | number,
  payload: {
    decision: ClientDecision;
    rejection_reason?: string;
    proposed_slot?: string;
  }
): Promise<any> {
  const { data } = await apiClient.patch(
    `/client/submissions/${submissionId}/decision`,
    payload
  );
  return data;
}
