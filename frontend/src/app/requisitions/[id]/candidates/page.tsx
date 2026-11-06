"use client";

import React, { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AuthGuard } from "@/components/AuthGuard";
import {
  useRequisition,
  useRankedCandidates,
  useSubmitToClient,
} from "@/hooks/useRequisitions";
import { CandidateCard } from "@/components/CandidateCard";
import { ScoreBadge, Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Candidate, RankedItem } from "@/lib/types";
import { markCandidateViewedApi } from "@/lib/api";
import {
  Search,
  UploadCloud,
  ListFilter,
  Kanban,
  Users,
  X,
  Send,
  Mail,
  Phone,
  Briefcase,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  RefreshCw,
} from "lucide-react";

export default function RankedCandidatesPage() {
  const params = useParams();
  const id = params?.id as string;

  const { data: requisition, isLoading: reqLoading } = useRequisition(id);
  const {
    data: rankedData,
    isLoading: rankedLoading,
    isError,
    error,
    refetch,
  } = useRankedCandidates(id);

  const submitMutation = useSubmitToClient(id);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [stageFilter, setStageFilter] = useState<string>("all");

  // Selected candidate drawer state
  const [selectedItem, setSelectedItem] = useState<RankedItem | null>(null);

  // Local viewed and submitted overrides
  const [viewedCandidateIds, setViewedCandidateIds] = useState<Set<string | number>>(
    new Set()
  );
  const [submittedIds, setSubmittedIds] = useState<Set<string | number>>(new Set());

  // Normalize ranked list items
  const candidatesList = useMemo(() => {
    if (!rankedData || !Array.isArray(rankedData)) return [];

    return rankedData.map((item: any, idx: number): RankedItem => {
      const cand = item.candidate || item;
      const candName = cand.full_name || cand.name || `Candidate #${idx + 1}`;
      const stage =
        item.pipeline_stage ||
        item.submission?.pipeline_stage ||
        cand.pipeline_stage ||
        "sourced";
      const subId =
        item.submission_id ||
        item.submission?.id ||
        item.id ||
        cand.id ||
        `sub-${idx}`;

      const normalizedCandidate: Candidate = {
        ...cand,
        id: cand.id || subId,
        name: candName,
        full_name: candName,
        ai_score: item.ai_score ?? cand.ai_score ?? 0,
        criteria_scores: item.criteria_scores ?? cand.criteria_scores,
        score_evidence: item.score_evidence ?? cand.score_evidence,
        pipeline_stage: stage,
        submitted_to_client: Boolean(
          item.submitted_to_client ||
            item.submission?.submitted_to_client ||
            stage === "client_reviewed" ||
            stage === "interview" ||
            stage === "offer" ||
            stage === "joined"
        ),
        viewed_by_recruiter: Boolean(
          item.recruiter_viewed ||
            item.submission?.recruiter_viewed ||
            item.viewed_by_recruiter
        ),
        client_decision:
          item.client_decision ||
          item.submission?.client_decision ||
          cand.client_decision,
      };

      return {
        id: normalizedCandidate.id,
        submission_id: subId,
        candidate: normalizedCandidate,
        ai_score: item.ai_score ?? normalizedCandidate.ai_score ?? 0,
        score_evidence: item.score_evidence ?? normalizedCandidate.score_evidence,
        criteria_scores: item.criteria_scores ?? normalizedCandidate.criteria_scores,
        submission: {
          id: subId,
          pipeline_stage: stage,
          submitted_to_client: Boolean(normalizedCandidate.submitted_to_client),
          viewed_by_recruiter: Boolean(normalizedCandidate.viewed_by_recruiter),
          client_decision: normalizedCandidate.client_decision as string,
        },
      };
    });
  }, [rankedData]);

  // Handle drawer open + mark viewed
  const handleOpenDetails = async (item: RankedItem) => {
    setSelectedItem(item);
    const candidateId = item.candidate.id;
    setViewedCandidateIds((prev) => new Set(prev).add(candidateId as any));

    try {
      await markCandidateViewedApi(candidateId);
    } catch {
      // Handled silently
    }
  };

  const handleSubmitToClient = async (item: RankedItem) => {
    const submissionId = item.submission_id || item.submission?.id || item.candidate.id;
    try {
      await submitMutation.mutateAsync(submissionId);
      setSubmittedIds((prev) => new Set(prev).add(submissionId as any));
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || "Failed to submit candidate to client");
    }
  };

  // Filtered and sorted candidates
  const filteredCandidates = useMemo(() => {
    return candidatesList
      .filter((item) => {
        const c = item.candidate;
        const nameStr = (c.full_name || c.name || "").toLowerCase();
        const roleStr = (c.current_role || "").toLowerCase();
        const q = searchQuery.toLowerCase();
        const matchesSearch = !q || nameStr.includes(q) || roleStr.includes(q);

        const currentStage = item.submission?.pipeline_stage || c.pipeline_stage || "sourced";
        const matchesStage = stageFilter === "all" || currentStage === stageFilter;

        return matchesSearch && matchesStage;
      })
      .sort((a, b) => {
        const scoreA = a.ai_score ?? a.candidate.ai_score ?? 0;
        const scoreB = b.ai_score ?? b.candidate.ai_score ?? 0;
        return scoreB - scoreA;
      });
  }, [candidatesList, searchQuery, stageFilter]);

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
          <span className="text-red-600 font-medium">Ranked Candidates</span>
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
                AI-ranked candidate pool scored against your requisition scorecard. View full profiles to submit candidates to clients.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Link href={`/requisitions/${id}/upload`}>
                <Button variant="outline" size="sm" leftIcon={<UploadCloud className="w-4 h-4" />}>
                  Upload More CVs
                </Button>
              </Link>
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
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-red-50 text-red-700 flex items-center gap-1.5"
            >
              <Users className="w-3.5 h-3.5" />
              <span>Ranked Candidates</span>
            </Link>
            <Link
              href={`/requisitions/${id}/pipeline`}
              className="px-3.5 py-2 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-1.5"
            >
              <Kanban className="w-3.5 h-3.5" />
              <span>Pipeline View</span>
            </Link>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name or role..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
            <span className="text-xs font-medium text-slate-500">Stage:</span>
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              className="px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 font-medium"
            >
              <option value="all">All Stages</option>
              <option value="sourced">Sourced</option>
              <option value="screened">Screened</option>
              <option value="submitted_to_client">Submitted to Client</option>
              <option value="client_reviewed">Client Reviewed</option>
              <option value="interview_scheduled">Interview</option>
              <option value="offer_made">Offer</option>
              <option value="joined">Joined</option>
            </select>
          </div>
        </div>

        {/* Loading Skeletons */}
        {rankedLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <div
                key={n}
                className="bg-white rounded-xl border border-slate-200 p-5 space-y-4"
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-2 w-3/4">
                    <Skeleton className="h-5 w-2/3" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                  <Skeleton className="h-6 w-12 rounded-full" />
                </div>
                <Skeleton className="h-16 w-full" />
                <div className="flex justify-between pt-3">
                  <Skeleton className="h-8 w-24" />
                  <Skeleton className="h-8 w-28" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="bg-white p-8 rounded-xl border border-red-200 text-center">
            <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-900">
              Failed to load ranked candidates
            </h3>
            <p className="text-sm text-slate-500 mt-1 mb-4">
              {(error as any)?.message || "Could not retrieve ranked candidates list."}
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

        {/* Empty State */}
        {!rankedLoading && !isError && filteredCandidates.length === 0 && (
          <EmptyState
            title="No CVs uploaded yet — start by uploading CVs above"
            description="Upload candidate resumes to see them automatically ranked with AI match scores and evidence quotes."
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

        {/* Candidates Grid */}
        {!rankedLoading && !isError && filteredCandidates.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredCandidates.map((item) => {
              const candidate = item.candidate;
              const subId = item.submission_id || item.submission?.id || candidate.id;
              const isViewed =
                item.submission?.viewed_by_recruiter ||
                candidate.viewed_by_recruiter ||
                viewedCandidateIds.has(candidate.id);
              const isSubmitted =
                item.submission?.submitted_to_client ||
                candidate.submitted_to_client ||
                submittedIds.has(subId);

              return (
                <CandidateCard
                  key={candidate.id}
                  candidate={{
                    ...candidate,
                    ai_score: item.ai_score ?? candidate.ai_score,
                    score_evidence: item.score_evidence ?? candidate.score_evidence,
                    pipeline_stage: item.submission?.pipeline_stage || candidate.pipeline_stage,
                  }}
                  mode="recruiter"
                  isViewed={isViewed}
                  isSubmitted={isSubmitted}
                  submissionId={subId}
                  onViewDetails={() => handleOpenDetails(item)}
                  onSubmitToClient={() => handleSubmitToClient(item)}
                  isSubmitting={submitMutation.isPending}
                />
              );
            })}
          </div>
        )}

        {/* Candidate Detail Slide-in Drawer */}
        {selectedItem && (
          <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-sm flex justify-end transition-opacity">
            <div className="w-full max-w-xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
              {/* Drawer Header */}
              <div className="p-6 border-b border-slate-200 flex items-start justify-between bg-slate-50/50">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-slate-900">
                      {selectedItem.candidate.full_name ||
                        selectedItem.candidate.name ||
                        "Candidate Profile"}
                    </h2>
                    <ScoreBadge score={selectedItem.ai_score ?? selectedItem.candidate.ai_score} size="md" />
                  </div>
                  <p className="text-sm font-medium text-slate-600 mt-1">
                    {selectedItem.candidate.current_role || "Role not specified"}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedItem(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
                  aria-label="Close drawer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Contact & Overview Info */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Candidate Profile Details
                  </h3>
                  <div className="grid grid-cols-2 gap-3 text-xs text-slate-700">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">
                        {selectedItem.candidate.email || "No email available"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{selectedItem.candidate.phone || "No phone available"}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        {selectedItem.candidate.experience_years !== undefined
                          ? `${selectedItem.candidate.experience_years} years exp`
                          : "Experience not parsed"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        {selectedItem.candidate.notice_days !== undefined
                          ? selectedItem.candidate.notice_days === 0
                            ? "Immediate joiner"
                            : `${selectedItem.candidate.notice_days} days notice`
                          : "Notice period not specified"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Skills tags */}
                {selectedItem.candidate.skills && selectedItem.candidate.skills.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Identified Skills
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedItem.candidate.skills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 text-xs font-medium bg-slate-100 text-slate-700 rounded-md"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Full Evidence Breakdown */}
                <div>
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                    AI Scoring Evidence & Quotes
                  </h3>

                  {(() => {
                    const criteriaList = Array.isArray(selectedItem.criteria_scores)
                      ? selectedItem.criteria_scores
                      : Array.isArray((selectedItem.candidate as any)?.criteria_scores)
                      ? (selectedItem.candidate as any).criteria_scores
                      : null;

                    if (criteriaList && criteriaList.length > 0) {
                      return (
                        <div className="space-y-3">
                          {criteriaList.map((crit: any, idx: number) => {
                            const quotes: string[] = crit.evidence_quotes || crit.evidence_lines || [];
                            const scoreVal =
                              typeof crit.score === "number"
                                ? Math.round(crit.score * 100)
                                : null;
                            return (
                              <div
                                key={idx}
                                className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-2"
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-xs text-slate-800">
                                      {crit.criterion_name || crit.name}
                                    </span>
                                    {crit.matched && (
                                      <span className="text-[10px] bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded font-medium">
                                        Matched
                                      </span>
                                    )}
                                  </div>
                                  {scoreVal !== null && (
                                    <Badge
                                      variant={
                                        scoreVal >= 70
                                          ? "success"
                                          : scoreVal >= 40
                                          ? "warning"
                                          : "danger"
                                      }
                                      size="sm"
                                    >
                                      {scoreVal}%
                                    </Badge>
                                  )}
                                </div>

                                {quotes.length > 0 ? (
                                  quotes.map((q: string, qIdx: number) => (
                                    <div
                                      key={qIdx}
                                      className="pl-3 border-l-2 border-blue-600 italic text-xs text-slate-600 bg-slate-50/70 py-1.5 pr-2 rounded-r"
                                    >
                                      &ldquo;{q}&rdquo;
                                    </div>
                                  ))
                                ) : (
                                  <div className="text-[11px] text-slate-400 italic">
                                    No direct evidence lines cited in CV
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      );
                    }

                    const evidenceObj =
                      selectedItem.score_evidence ||
                      selectedItem.candidate.score_evidence;
                    if (evidenceObj && typeof evidenceObj === "object") {
                      return (
                        <div className="space-y-3">
                          {Object.entries(evidenceObj).map(
                            ([criterion, data]: [string, any], idx: number) => {
                              const quotes: string[] = [];
                              if (typeof data === "string") quotes.push(data);
                              else if (Array.isArray(data?.evidence_lines))
                                quotes.push(...data.evidence_lines);
                              else if (typeof data?.evidence_lines === "string")
                                quotes.push(data.evidence_lines);
                              else if (data?.reasoning) quotes.push(data.reasoning);

                              return (
                                <div
                                  key={idx}
                                  className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-2"
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="font-semibold text-xs text-slate-800">
                                      {criterion}
                                    </span>
                                    {data?.score !== undefined && (
                                      <Badge variant="info" size="sm">
                                        Score: {data.score}
                                      </Badge>
                                    )}
                                  </div>

                                  {quotes.map((q, qIdx) => (
                                    <div
                                      key={qIdx}
                                      className="pl-3 border-l-2 border-blue-600 italic text-xs text-slate-600 bg-slate-50/70 py-1.5 pr-2 rounded-r"
                                    >
                                      &ldquo;{q}&rdquo;
                                    </div>
                                  ))}
                                </div>
                              );
                            }
                          )}
                        </div>
                      );
                    }

                    return (
                      <p className="text-xs text-slate-400 italic">
                        No detailed criteria breakdown recorded.
                      </p>
                    );
                  })()}
                </div>
              </div>

              {/* Drawer Footer Actions */}
              <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
                <Button
                  variant="outline"
                  onClick={() => setSelectedItem(null)}
                >
                  Close
                </Button>

                {(() => {
                  const subId =
                    selectedItem.submission_id ||
                    selectedItem.submission?.id ||
                    selectedItem.candidate.id;
                  const isSubmitted =
                    selectedItem.submission?.submitted_to_client ||
                    selectedItem.candidate.submitted_to_client ||
                    submittedIds.has(subId);

                  return (
                    <Button
                      variant={isSubmitted ? "secondary" : "primary"}
                      disabled={isSubmitted || submitMutation.isPending}
                      isLoading={submitMutation.isPending}
                      onClick={() => handleSubmitToClient(selectedItem)}
                      leftIcon={<Send className="w-4 h-4" />}
                    >
                      {isSubmitted ? "Submitted to Client" : "Submit to Client"}
                    </Button>
                  );
                })()}
              </div>
            </div>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
