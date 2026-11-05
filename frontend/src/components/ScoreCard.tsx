import React from "react";
import { ScoreBadge } from "./ui/Badge";
import { CandidateScoreEvidence } from "@/lib/types";
import { Quote } from "lucide-react";

interface ScoreCardProps {
  score?: number | null;
  evidence?: CandidateScoreEvidence | any[] | null;
  criteriaScores?: any[] | null;
  maxSnippets?: number;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({
  score,
  evidence,
  criteriaScores,
  maxSnippets = 2,
}) => {
  // Extract evidence snippets
  const snippets: { criterion: string; quote: string }[] = [];

  // 1. If criteriaScores array is provided (from backend criteria_scores)
  const listToInspect = Array.isArray(criteriaScores)
    ? criteriaScores
    : Array.isArray(evidence)
    ? evidence
    : null;

  if (listToInspect) {
    listToInspect.forEach((item: any) => {
      if (!item) return;
      const criterion = item.criterion_name || item.name || "Criterion";
      const quotes = item.evidence_quotes || item.evidence_lines || [];
      if (Array.isArray(quotes) && quotes.length > 0) {
        snippets.push({ criterion, quote: quotes[0] });
      } else if (typeof quotes === "string" && quotes) {
        snippets.push({ criterion, quote: quotes });
      }
    });
  } else if (evidence && typeof evidence === "object") {
    Object.entries(evidence).forEach(([criterion, data]) => {
      if (!data) return;
      if (typeof data === "string") {
        snippets.push({ criterion, quote: data });
      } else if (typeof data === "object") {
        if (Array.isArray(data.evidence_lines)) {
          data.evidence_lines.forEach((line: string) => {
            if (line) snippets.push({ criterion, quote: line });
          });
        } else if (Array.isArray(data.evidence_quotes)) {
          data.evidence_quotes.forEach((line: string) => {
            if (line) snippets.push({ criterion, quote: line });
          });
        } else if (typeof data.evidence_lines === "string") {
          snippets.push({ criterion, quote: data.evidence_lines });
        } else if (data.reasoning) {
          snippets.push({ criterion, quote: data.reasoning });
        }
      }
    });
  }

  const displayedSnippets = snippets.slice(0, maxSnippets);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <ScoreBadge score={score} size="md" />
        <span className="text-xs text-slate-500 font-medium">Match Score</span>
      </div>

      {displayedSnippets.length > 0 ? (
        <div className="space-y-1.5 mt-2">
          {displayedSnippets.map((item, idx) => (
            <div
              key={idx}
              className="pl-2.5 border-l-2 border-blue-600 italic text-xs text-slate-500 leading-relaxed bg-slate-50/60 py-1 pr-2 rounded-r"
            >
              <span className="font-semibold text-slate-700 not-italic mr-1.5 text-[11px] uppercase tracking-wider">
                {item.criterion}:
              </span>
              &ldquo;{item.quote}&rdquo;
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-400 italic">No evidence quotes available</p>
      )}
    </div>
  );
};
