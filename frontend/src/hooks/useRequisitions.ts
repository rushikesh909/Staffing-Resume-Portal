"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getRequisitionsApi,
  getRequisitionApi,
  getClientsApi,
  createRequisitionApi,
  updateScorecardApi,
  getRankedCandidatesApi,
  getPipelineSummaryApi,
  updateSubmissionStageApi,
  submitToClientApi,
  getClientRequisitionsApi,
  getClientSubmissionsApi,
  submitClientDecisionApi,
} from "@/lib/api";
import { PipelineStage, ClientDecision } from "@/lib/types";

export function useRequisitions() {
  return useQuery({
    queryKey: ["requisitions"],
    queryFn: getRequisitionsApi,
  });
}

export function useRequisition(id: number | string) {
  return useQuery({
    queryKey: ["requisition", String(id)],
    queryFn: () => getRequisitionApi(id),
    enabled: Boolean(id),
  });
}

export function useClients() {
  return useQuery({
    queryKey: ["clients"],
    queryFn: getClientsApi,
  });
}

export function useCreateRequisition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRequisitionApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["requisitions"] });
    },
  });
}

export function useUpdateScorecard(requisitionId: number | string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scorecard: any) => updateScorecardApi(requisitionId, scorecard),
    onSuccess: (data) => {
      queryClient.setQueryData(["requisition", String(requisitionId)], data);
      queryClient.invalidateQueries({ queryKey: ["requisition", String(requisitionId)] });
    },
  });
}

export function useRankedCandidates(requisitionId: number | string) {
  return useQuery({
    queryKey: ["ranked-candidates", String(requisitionId)],
    queryFn: () => getRankedCandidatesApi(requisitionId),
    enabled: Boolean(requisitionId),
  });
}

export function usePipelineSummary(requisitionId: number | string) {
  return useQuery({
    queryKey: ["pipeline-summary", String(requisitionId)],
    queryFn: () => getPipelineSummaryApi(requisitionId),
    enabled: Boolean(requisitionId),
  });
}

export function useUpdateStage(requisitionId?: number | string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ submissionId, stage }: { submissionId: number; stage: PipelineStage }) =>
      updateSubmissionStageApi(submissionId, stage),
    onSuccess: () => {
      if (requisitionId) {
        queryClient.invalidateQueries({ queryKey: ["pipeline-summary", String(requisitionId)] });
        queryClient.invalidateQueries({ queryKey: ["ranked-candidates", String(requisitionId)] });
      }
    },
  });
}

export function useSubmitToClient(requisitionId?: number | string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (submissionId: number) => submitToClientApi(submissionId),
    onSuccess: () => {
      if (requisitionId) {
        queryClient.invalidateQueries({ queryKey: ["ranked-candidates", String(requisitionId)] });
        queryClient.invalidateQueries({ queryKey: ["pipeline-summary", String(requisitionId)] });
      }
    },
  });
}

export function useClientRequisitions() {
  return useQuery({
    queryKey: ["client-requisitions"],
    queryFn: getClientRequisitionsApi,
  });
}

export function useClientSubmissions(requisitionId: number | string) {
  return useQuery({
    queryKey: ["client-submissions", String(requisitionId)],
    queryFn: () => getClientSubmissionsApi(requisitionId),
    enabled: Boolean(requisitionId),
  });
}

export function useSubmitClientDecision(requisitionId?: number | string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      submissionId,
      data,
    }: {
      submissionId: number;
      data: { decision: ClientDecision; rejection_reason?: string; proposed_slot?: string };
    }) => submitClientDecisionApi(submissionId, data),
    onSuccess: () => {
      if (requisitionId) {
        queryClient.invalidateQueries({ queryKey: ["client-submissions", String(requisitionId)] });
      }
    },
  });
}
