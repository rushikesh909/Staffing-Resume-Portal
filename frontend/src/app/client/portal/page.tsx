"use client";

import React, { useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import {
  useClientRequisitions,
  useClientSubmissions,
  useSubmitClientDecision,
} from "@/hooks/useRequisitions";
import { CandidateCard } from "@/components/CandidateCard";
import { DecisionModal } from "@/components/DecisionModal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Candidate, ClientDecision } from "@/lib/types";
import {
  Briefcase,
  Users,
  AlertTriangle,
  RefreshCw,
  Building2,
  CheckCircle2,
  Calendar,
} from "lucide-react";

export default function ClientPortalPage() {
  const {
    data: requisitions,
    isLoading: reqsLoading,
    isError: reqsError,
    error: reqError,
    refetch: refetchReqs,
  } = useClientRequisitions();

  const [selectedReqId, setSelectedReqId] = useState<number | null>(null);

  // Active requisition ID
  const activeReqId =
    selectedReqId ?? (requisitions && requisitions.length > 0 ? requisitions[0].id : null);

  const {
    data: submissions,
    isLoading: subsLoading,
    isError: subsError,
    error: subError,
    refetch: refetchSubs,
  } = useClientSubmissions(activeReqId ?? 0);

  const decisionMutation = useSubmitClientDecision(activeReqId ?? undefined);

  // Decision Modal State
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    submissionId: number;
    candidateName: string;
    decisionType: ClientDecision | null;
  }>({
    isOpen: false,
    submissionId: 0,
    candidateName: "",
    decisionType: null,
  });

  const handleOpenDecision = (
    subId: number,
    candidateName: string,
    decisionType: ClientDecision
  ) => {
    // If shortlisted directly, we can either submit immediately or show confirmation
    setModalState({
      isOpen: true,
      submissionId: subId,
      candidateName,
      decisionType,
    });
  };

  const handleConfirmDecision = async (data: {
    decision: ClientDecision;
    rejection_reason?: string;
    proposed_slot?: string;
  }) => {
    await decisionMutation.mutateAsync({
      submissionId: modalState.submissionId,
      data,
    });
  };

  const activeRequisition = requisitions?.find((r) => r.id === activeReqId);

  // Normalize candidate submissions list
  const candidateSubmissions = React.useMemo(() => {
    if (!submissions || !Array.isArray(submissions)) return [];

    return submissions.map((item: any) => {
      // Could be CandidatePortalOut or {submission, candidate}
      if (item.candidate) {
        return {
          submissionId: item.submission?.id || item.id,
          candidate: item.candidate,
          ai_score: item.ai_score ?? item.candidate.ai_score,
          score_evidence: item.score_evidence ?? item.candidate.score_evidence,
          pipeline_stage: item.submission?.pipeline_stage || item.candidate.pipeline_stage,
          client_decision: item.submission?.client_decision || item.client_decision,
        };
      } else {
        return {
          submissionId: item.id,
          candidate: {
            ...item,
            name: item.name || `Candidate #${item.id}`,
          } as Candidate,
          ai_score: item.ai_score,
          score_evidence: item.score_evidence,
          pipeline_stage: item.pipeline_stage,
          client_decision: item.client_decision,
        };
      }
    });
  }, [submissions]);

  return (
    <AuthGuard allowedRoles={["client_hiring_manager"]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Header */}
        <div className="pb-6 border-b border-slate-200">
          <div className="flex items-center gap-2 text-blue-600 text-xs font-semibold uppercase tracking-wider mb-1">
            <Building2 className="w-4 h-4" />
            <span>Client Hiring Portal</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Candidate Submissions Review
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Review pre-screened, AI-scored candidates submitted by your staffing agency. Shortlist for interviews or provide feedback.
          </p>
        </div>

        {/* Requisitions Switcher Tabs */}
        {reqsLoading && (
          <div className="flex gap-2 mt-6">
            <Skeleton className="h-10 w-48 rounded-lg" />
            <Skeleton className="h-10 w-48 rounded-lg" />
          </div>
        )}

        {reqsError && (
          <div className="mt-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-center justify-between">
            <span className="text-xs text-red-700 font-medium">
              Failed to load requisitions: {(reqError as any)?.message}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchReqs()}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Retry
            </Button>
          </div>
        )}

        {!reqsLoading && requisitions && requisitions.length > 0 && (
          <div className="flex items-center gap-2 mt-6 overflow-x-auto pb-2 border-b border-slate-200">
            {requisitions.map((req) => {
              const isSelected = req.id === activeReqId;
              return (
                <button
                  key={req.id}
                  onClick={() => setSelectedReqId(req.id)}
                  className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap flex items-center gap-2 ${
                    isSelected
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200"
                  }`}
                >
                  <Briefcase className="w-3.5 h-3.5" />
                  <span>{req.title}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Requisition Status Subheader */}
        {activeRequisition && (
          <div className="mt-6 bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  {activeRequisition.title}
                </h2>
                <Badge variant="success" size="sm">
                  {activeRequisition.status}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Role ID: #{activeRequisition.id} • Assigned to your hiring team
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span className="font-semibold text-slate-800">
                {candidateSubmissions.length}
              </span>
              <span>candidates ready for your review</span>
            </div>
          </div>
        )}

        {/* Candidates Section */}
        <div className="mt-8">
          {/* Loading state */}
          {subsLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {[1, 2, 3].map((n) => (
                <div
                  key={n}
                  className="bg-white rounded-xl border border-slate-200 p-5 space-y-4"
                >
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-16 w-full" />
                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {subsError && (
            <div className="bg-white p-8 rounded-xl border border-red-200 text-center">
              <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-slate-900">
                Failed to load candidate submissions
              </h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">
                {(subError as any)?.message || "Could not retrieve candidate submissions."}
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchSubs()}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Retry
              </Button>
            </div>
          )}

          {/* Empty State */}
          {!subsLoading && !subsError && candidateSubmissions.length === 0 && (
            <EmptyState
              title="No candidates submitted to review yet"
              description="Your staffing recruiter is currently sourcing and screening candidates against the rubric. When profiles are submitted, they will appear here for review."
              icon={<Users className="w-6 h-6 text-blue-600" />}
            />
          )}

          {/* Responsive Candidate Card Grid (Mobile-First) */}
          {!subsLoading && !subsError && candidateSubmissions.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {candidateSubmissions.map((item) => (
                <CandidateCard
                  key={item.submissionId}
                  candidate={{
                    ...item.candidate,
                    ai_score: item.ai_score ?? item.candidate.ai_score,
                    score_evidence: item.score_evidence ?? item.candidate.score_evidence,
                    client_decision: item.client_decision,
                    pipeline_stage: item.pipeline_stage,
                  }}
                  mode="client"
                  submissionId={item.submissionId}
                  onDecision={(decisionType) =>
                    handleOpenDecision(
                      item.submissionId,
                      item.candidate.name,
                      decisionType
                    )
                  }
                />
              ))}
            </div>
          )}
        </div>

        {/* Decision Modal (Shortlist / Reject / Interview Slot) */}
        <DecisionModal
          isOpen={modalState.isOpen}
          decisionType={modalState.decisionType}
          candidateName={modalState.candidateName}
          onClose={() =>
            setModalState((prev) => ({ ...prev, isOpen: false, decisionType: null }))
          }
          onSubmit={handleConfirmDecision}
          isLoading={decisionMutation.isPending}
        />
      </div>
    </AuthGuard>
  );
}
