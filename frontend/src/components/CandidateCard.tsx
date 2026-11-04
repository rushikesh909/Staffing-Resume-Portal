import React from "react";
import { Candidate, ClientDecision } from "@/lib/types";
import { ScoreBadge, Badge } from "./ui/Badge";
import { ScoreCard } from "./ScoreCard";
import { Button } from "./ui/Button";
import {
  Briefcase,
  Clock,
  Send,
  Eye,
  CheckCircle,
  XCircle,
  Calendar,
  Lock,
  Mail,
  Phone,
  AlertCircle,
} from "lucide-react";

interface CandidateCardProps {
  candidate: Candidate;
  mode?: "recruiter" | "client";
  isViewed?: boolean;
  isSubmitted?: boolean;
  submissionId?: number;
  onViewDetails?: () => void;
  onSubmitToClient?: () => void;
  isSubmitting?: boolean;
  onDecision?: (decision: ClientDecision) => void;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({
  candidate,
  mode = "recruiter",
  isViewed = false,
  isSubmitted = false,
  onViewDetails,
  onSubmitToClient,
  isSubmitting = false,
  onDecision,
}) => {
  const isClient = mode === "client";
  const stage = candidate.pipeline_stage || "sourced";
  const decision = candidate.client_decision;

  const getStageBadge = (stg: string) => {
    const formatted = stg.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    switch (stg) {
      case "joined":
      case "offer_made":
        return <Badge variant="success" size="sm">{formatted}</Badge>;
      case "interview_scheduled":
      case "submitted_to_client":
        return <Badge variant="info" size="sm">{formatted}</Badge>;
      case "client_reviewed":
        return <Badge variant="warning" size="sm">{formatted}</Badge>;
      default:
        return <Badge variant="default" size="sm">{formatted}</Badge>;
    }
  };

  const getDecisionBadge = (dec: string) => {
    switch (dec) {
      case "shortlisted":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5" />
            Shortlisted
          </span>
        );
      case "rejected":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" />
            Rejected
          </span>
        );
      case "interview_proposed":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Calendar className="w-3.5 h-3.5" />
            Interview Slot Proposed
          </span>
        );
      default:
        return null;
    }
  };

  const canShowContacts = !isClient || stage === "interview_scheduled" || stage === "offer_made" || stage === "joined";

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition flex flex-col justify-between">
      <div>
        {/* Top Header: Candidate Name, Role & Stage/Decision Badge */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-base font-bold text-slate-900 truncate flex items-center gap-2">
              <span>{candidate.name}</span>
              {isSubmitted && !isClient && (
                <Badge variant="info" size="sm">
                  Client Review
                </Badge>
              )}
            </h3>
            <p className="text-xs text-slate-600 font-medium mt-0.5 flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5 text-slate-400" />
              <span>{candidate.current_role || "Role not specified"}</span>
            </p>
          </div>

          <div className="flex flex-col items-end gap-1 flex-shrink-0">
            {!isClient ? getStageBadge(stage) : decision ? getDecisionBadge(decision) : (
              <Badge variant="neutral" size="sm">Pending Review</Badge>
            )}
          </div>
        </div>

        {/* Experience & Notice info pills */}
        <div className="flex flex-wrap items-center gap-2 mt-3 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 font-medium">
            <Clock className="w-3 h-3 text-slate-500" />
            {candidate.experience_years !== undefined && candidate.experience_years !== null
              ? `${candidate.experience_years} yrs exp`
              : "Experience N/A"}
          </span>

          {candidate.notice_days !== undefined && candidate.notice_days !== null && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 font-medium">
              {candidate.notice_days === 0 ? "Immediate Joiner" : `${candidate.notice_days} days notice`}
            </span>
          )}

          {/* Contact masking for Client */}
          {!canShowContacts ? (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-amber-50 text-amber-700 text-[11px] font-medium border border-amber-200">
              <Lock className="w-3 h-3" />
              <span>Contacts masked until interview</span>
            </span>
          ) : (
            candidate.email && (
              <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                <Mail className="w-3 h-3" />
                <span className="truncate max-w-[150px]">{candidate.email}</span>
              </span>
            )
          )}
        </div>

        {/* Score & Evidence Snippets Section */}
        <div className="mt-4 pt-3 border-t border-slate-100">
          <ScoreCard
            score={candidate.ai_score}
            evidence={candidate.score_evidence}
            maxSnippets={2}
          />
        </div>
      </div>

      {/* Footer Actions */}
      <div className="mt-5 pt-4 border-t border-slate-100">
        {!isClient ? (
          /* Recruiter Actions */
          <div className="flex items-center justify-between gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={onViewDetails}
              leftIcon={<Eye className="w-3.5 h-3.5" />}
            >
              View Details
            </Button>

            <div className="flex items-center gap-2">
              <Button
                variant={isSubmitted ? "secondary" : "primary"}
                size="sm"
                disabled={!isViewed || isSubmitted || isSubmitting}
                isLoading={isSubmitting}
                onClick={onSubmitToClient}
                leftIcon={<Send className="w-3.5 h-3.5" />}
                title={
                  !isViewed
                    ? "View full candidate profile first to enable submission"
                    : isSubmitted
                    ? "Candidate already submitted to client"
                    : "Submit candidate to client portal"
                }
              >
                {isSubmitted ? "Submitted to Client" : "Submit to Client"}
              </Button>
            </div>
          </div>
        ) : (
          /* Client Actions */
          <div className="space-y-2">
            {!decision ? (
              <div className="grid grid-cols-3 gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onDecision?.("shortlisted")}
                  className="bg-emerald-600 hover:bg-emerald-700 text-xs px-2"
                >
                  Shortlist
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDecision?.("interview_proposed")}
                  className="text-xs px-2"
                >
                  Interview
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDecision?.("rejected")}
                  className="text-red-600 hover:bg-red-50 hover:border-red-200 text-xs px-2"
                >
                  Reject
                </Button>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500 font-medium">
                  Review complete
                </span>
                <button
                  type="button"
                  onClick={() => onDecision?.("interview_proposed")}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Change decision
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
