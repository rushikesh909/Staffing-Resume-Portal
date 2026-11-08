"use client";

import React, { useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AuthGuard } from "@/components/AuthGuard";
import {
  useRequisition,
  useRankedCandidates,
  useUpdateStage,
} from "@/hooks/useRequisitions";
import { PipelineBoard } from "@/components/PipelineBoard";
import { Candidate, PipelineStage } from "@/lib/types";
import { ScoreBadge, Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { deleteRequisitionApi } from "@/lib/api";
import {
  UploadCloud,
  ListFilter,
  Kanban,
  Users,
  X,
  Clock,
  Briefcase,
  Mail,
  Phone,
  RefreshCw,
  AlertCircle,
  FileText,
  Trash2,
} from "lucide-react";

export default function PipelinePage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteRequisition = async () => {
    if (window.confirm(`Are you sure you want to delete requisition "${requisition?.title}" and all its candidate submissions?`)) {
      try {
        setIsDeleting(true);
        await deleteRequisitionApi(id);
        router.push("/dashboard");
      } catch (err: any) {
        alert("Failed to delete requisition: " + (err?.response?.data?.detail || err.message));
        setIsDeleting(false);
      }
    }
  };

  const { data: requisition, isLoading: reqLoading } = useRequisition(id);
  const {
    data: candidatesData,
    isLoading: candsLoading,
    isError,
    error,
    refetch,
  } = useRankedCandidates(id);

  const updateStageMutation = useUpdateStage(id);

  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(
    null
  );

  // Normalize pipeline candidates
  const pipelineCandidates = useMemo(() => {
    if (!candidatesData || !Array.isArray(candidatesData)) return [];

    return candidatesData.map((item: any) => {
      const candidate: Candidate = item.candidate || item;
      const candName = candidate.full_name || candidate.name || "Candidate";
      const stage: PipelineStage =
        item.pipeline_stage ||
        item.submission?.pipeline_stage ||
        candidate.pipeline_stage ||
        "sourced";
      const submissionId: string | number =
        item.submission_id || item.submission?.id || candidate.id;

      return {
        submissionId,
        candidate: {
          ...candidate,
          name: candName,
          full_name: candName,
          ai_score: item.ai_score ?? candidate.ai_score,
          score_evidence: item.score_evidence ?? candidate.score_evidence,
          criteria_scores: item.criteria_scores ?? (candidate as any).criteria_scores,
        },
        stage,
      };
    });
  }, [candidatesData]);

  const handleMoveStage = async (
    submissionId: string | number,
    nextStage: PipelineStage
  ) => {
    try {
      await updateStageMutation.mutateAsync({
        submissionId: submissionId as any,
        stage: nextStage,
      });
      refetch();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || "Failed to update pipeline stage");
    }
  };

  return (
    <AuthGuard allowedRoles={["recruiter", "delivery_head"]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Breadcrumb navigation */}
        <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
          <Link href="/dashboard" className="hover:text-slate-900 transition">
            Dashboard
          </Link>
          <span>/</span>
          <span className="text-slate-800 font-medium truncate max-w-xs">
            {requisition?.title || "Requisition"}
          </span>
          <span>/</span>
          <span className="text-red-600 font-medium">Pipeline Board</span>
        </div>

        {/* Requisition Header & Context */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-900">
                  {reqLoading ? <Skeleton className="h-7 w-64" /> : requisition?.title}
                </h1>
                {requisition && (
                  <Badge variant="success" size="sm">
                    {requisition.status}
                  </Badge>
                )}
              </div>
              <p className="mt-1 text-sm text-slate-500">
                Track candidate progression across all stages from Sourced to Joined.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Link href={`/requisitions/${id}/upload`}>
                <Button variant="outline" size="sm" leftIcon={<UploadCloud className="w-4 h-4" />}>
                  Upload CVs
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeleteRequisition}
                disabled={isDeleting}
                className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 border-rose-200"
                leftIcon={<Trash2 className="w-4 h-4 text-rose-500" />}
              >
                {isDeleting ? "Deleting..." : "Delete Requisition"}
              </Button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 border-t border-slate-100 mt-6 pt-3 overflow-x-auto">
            <Link
              href={`/requisitions/${id}/scorecard`}
              className="px-3.5 py-2 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-1.5"
            >
              <ListFilter className="w-3.5 h-3.5" />
              <span>Scorecard Editor</span>
            </Link>
            <Link
              href={`/requisitions/${id}/upload`}
              className="px-3.5 py-2 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-1.5"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload CVs</span>
            </Link>
            <Link
              href={`/requisitions/${id}/candidates`}
              className="px-3.5 py-2 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-1.5"
            >
              <Users className="w-3.5 h-3.5" />
              <span>Ranked Candidates</span>
            </Link>
            <Link
              href={`/requisitions/${id}/pipeline`}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-red-50 text-red-700 flex items-center gap-1.5"
            >
              <Kanban className="w-3.5 h-3.5" />
              <span>Pipeline View</span>
            </Link>
          </div>
        </div>

        {/* Board Content */}
        {candsLoading && (
          <div className="flex gap-4 overflow-x-auto pb-4">
            {[1, 2, 3, 4, 5].map((n) => (
              <div
                key={n}
                className="w-72 bg-slate-100 rounded-xl p-3 flex-shrink-0 space-y-3"
              >
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="bg-white p-8 rounded-xl border border-red-200 text-center">
            <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-900">
              Failed to load pipeline
            </h3>
            <p className="text-sm text-slate-500 mt-1 mb-4">
              {(error as any)?.message || "Could not retrieve candidate pipeline data."}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              leftIcon={<RefreshCw className="w-4 h-4" />}
            >
              Retry
            </Button>
          </div>
        )}

        {!candsLoading && !isError && pipelineCandidates.length === 0 && (
          <EmptyState
            title="No candidates in pipeline"
            description="Upload CVs to this requisition to populate the pipeline board."
            icon={<FileText className="w-6 h-6 text-blue-600" />}
            action={
              <Link href={`/requisitions/${id}/upload`}>
                <Button leftIcon={<UploadCloud className="w-4 h-4" />}>
                  Upload CVs
                </Button>
              </Link>
            }
          />
        )}

        {!candsLoading && !isError && pipelineCandidates.length > 0 && (
          <PipelineBoard
            candidates={pipelineCandidates}
            onSelectCandidate={(c) => setSelectedCandidate(c)}
            onMoveStage={handleMoveStage}
            isUpdating={updateStageMutation.isPending}
          />
        )}

        {/* Candidate Detail Drawer */}
        {selectedCandidate && (
          <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-sm flex justify-end">
            <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
              <div className="p-5 border-b border-slate-200 flex items-start justify-between bg-slate-50">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    {selectedCandidate.full_name ||
                      selectedCandidate.name ||
                      "Candidate Profile"}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {selectedCandidate.current_role || "Role not specified"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedCandidate(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-xs font-medium text-slate-600">
                    AI Match Score
                  </span>
                  <ScoreBadge score={selectedCandidate.ai_score} size="md" />
                </div>

                <div className="space-y-2 text-xs text-slate-600">
                  <div className="flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    <span>{selectedCandidate.email || "No email"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{selectedCandidate.phone || "No phone"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {selectedCandidate.experience_years !== undefined
                        ? `${selectedCandidate.experience_years} years experience`
                        : "Experience not specified"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {selectedCandidate.notice_days !== undefined
                        ? `${selectedCandidate.notice_days} days notice`
                        : "Notice not specified"}
                    </span>
                  </div>
                </div>

                {selectedCandidate.skills && selectedCandidate.skills.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 mb-1.5">
                      Extracted Skills
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {selectedCandidate.skills.map((s, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 text-xs bg-slate-100 text-slate-700 rounded"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 border-t border-slate-200">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setSelectedCandidate(null)}
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
