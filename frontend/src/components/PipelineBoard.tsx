"use client";

import React from "react";
import { Candidate, PipelineStage } from "@/lib/types";
import { ScoreBadge, Badge } from "./ui/Badge";
import { Clock, Briefcase, ChevronRight, User } from "lucide-react";

interface PipelineCandidate {
  submissionId: number;
  candidate: Candidate;
  stage: PipelineStage;
}

interface PipelineBoardProps {
  candidates: PipelineCandidate[];
  onSelectCandidate: (candidate: Candidate) => void;
  onMoveStage: (submissionId: number, nextStage: PipelineStage) => void;
  isUpdating?: boolean;
}

export const STAGES: { id: PipelineStage; label: string; color: string }[] = [
  { id: "sourced", label: "Sourced", color: "border-slate-300" },
  { id: "screened", label: "Screened", color: "border-blue-400" },
  { id: "submitted_to_client", label: "Submitted to Client", color: "border-indigo-400" },
  { id: "client_reviewed", label: "Client Reviewed", color: "border-amber-400" },
  { id: "interview_scheduled", label: "Interview", color: "border-purple-400" },
  { id: "offer_made", label: "Offer", color: "border-emerald-400" },
  { id: "joined", label: "Joined", color: "border-green-600" },
];

export const PipelineBoard: React.FC<PipelineBoardProps> = ({
  candidates,
  onSelectCandidate,
  onMoveStage,
  isUpdating = false,
}) => {
  return (
    <div className="flex gap-4 overflow-x-auto pb-6 pt-2 select-none min-h-[550px]">
      {STAGES.map((stageObj, stageIndex) => {
        const stageCandidates = candidates.filter(
          (c) => (c.stage || "sourced") === stageObj.id
        );

        const nextStage =
          stageIndex < STAGES.length - 1 ? STAGES[stageIndex + 1].id : null;

        return (
          <div
            key={stageObj.id}
            className="flex-shrink-0 w-72 bg-slate-100/70 rounded-xl p-3 flex flex-col border border-slate-200"
          >
            {/* Column Header */}
            <div className="flex items-center justify-between pb-3 px-1 border-b border-slate-200">
              <span className="text-xs font-bold text-slate-800 tracking-tight">
                {stageObj.label}
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white text-slate-600 border border-slate-200">
                {stageCandidates.length}
              </span>
            </div>

            {/* Column Content */}
            <div className="flex-1 mt-3 space-y-3 overflow-y-auto max-h-[600px] pr-1">
              {stageCandidates.length === 0 ? (
                <div className="h-32 border-2 border-dashed border-slate-200 rounded-lg flex items-center justify-center p-4 text-center">
                  <span className="text-xs text-slate-400">
                    No candidates in {stageObj.label.toLowerCase()}
                  </span>
                </div>
              ) : (
                stageCandidates.map((item) => {
                  const c = item.candidate;
                  return (
                    <div
                      key={item.submissionId}
                      className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition cursor-pointer space-y-2 group"
                      onClick={() => onSelectCandidate(c)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <h4 className="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition truncate">
                            {c.name}
                          </h4>
                          <p className="text-[11px] text-slate-500 truncate mt-0.5">
                            {c.current_role || "Role not specified"}
                          </p>
                        </div>
                        <ScoreBadge score={c.ai_score} size="sm" />
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                        <span>
                          {c.experience_years !== undefined
                            ? `${c.experience_years}y exp`
                            : "N/A"}
                        </span>

                        {nextStage && (
                          <button
                            type="button"
                            disabled={isUpdating}
                            onClick={(e) => {
                              e.stopPropagation();
                              onMoveStage(item.submissionId, nextStage);
                            }}
                            className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 px-2 py-0.5 rounded transition disabled:opacity-50"
                            title={`Advance to ${nextStage}`}
                          >
                            <span>Advance</span>
                            <ChevronRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
