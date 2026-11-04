"use client";

import React, { useState } from "react";
import { ClientDecision } from "@/lib/types";
import { Button } from "./ui/Button";
import { Textarea } from "./ui/Input";
import { Calendar, XCircle, CheckCircle, X, Clock } from "lucide-react";

interface DecisionModalProps {
  isOpen: boolean;
  decisionType: ClientDecision | null;
  candidateName: string;
  onClose: () => void;
  onSubmit: (data: {
    decision: ClientDecision;
    rejection_reason?: string;
    proposed_slot?: string;
  }) => Promise<void>;
  isLoading?: boolean;
}

export const DecisionModal: React.FC<DecisionModalProps> = ({
  isOpen,
  decisionType,
  candidateName,
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const [rejectionReason, setRejectionReason] = useState("");
  const [proposedSlot, setProposedSlot] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !decisionType) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (decisionType === "rejected" && !rejectionReason.trim()) {
      setError("Please provide a reason for rejection to help refine candidate matching.");
      return;
    }

    if (decisionType === "interview_proposed" && !proposedSlot) {
      setError("Please select a proposed interview date and time slot.");
      return;
    }

    try {
      await onSubmit({
        decision: decisionType,
        rejection_reason: decisionType === "rejected" ? rejectionReason : undefined,
        proposed_slot: decisionType === "interview_proposed" ? proposedSlot : undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to submit decision");
    }
  };

  const getHeaderInfo = () => {
    switch (decisionType) {
      case "shortlisted":
        return {
          title: "Shortlist Candidate",
          description: `Confirm shortlisting ${candidateName} for subsequent rounds.`,
          icon: <CheckCircle className="w-5 h-5 text-emerald-600" />,
          buttonText: "Confirm Shortlist",
          variant: "primary" as const,
        };
      case "rejected":
        return {
          title: "Reject Candidate",
          description: `Provide feedback on why ${candidateName} is not a fit for this requisition.`,
          icon: <XCircle className="w-5 h-5 text-rose-600" />,
          buttonText: "Confirm Rejection",
          variant: "danger" as const,
        };
      case "interview_proposed":
        return {
          title: "Propose Interview Slot",
          description: `Select your preferred interview time for ${candidateName}. Contact details will be unmasked.`,
          icon: <Calendar className="w-5 h-5 text-blue-600" />,
          buttonText: "Send Interview Slot",
          variant: "primary" as const,
        };
    }
  };

  const info = getHeaderInfo();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-slate-50 flex items-center justify-center">
              {info.icon}
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                {info.title}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">{info.description}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
              {error}
            </div>
          )}

          {decisionType === "rejected" && (
            <div>
              <Textarea
                label="Rejection Reason (Required)"
                placeholder="Explain missing requirements (e.g., lacks required years in FastAPI, notice period too long)..."
                rows={4}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                required
              />
            </div>
          )}

          {decisionType === "interview_proposed" && (
            <div>
              <label
                htmlFor="interview_slot"
                className="block text-sm font-medium text-slate-700 mb-1"
              >
                Proposed Interview Date & Time
              </label>
              <div className="relative">
                <input
                  id="interview_slot"
                  type="datetime-local"
                  value={proposedSlot}
                  onChange={(e) => setProposedSlot(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
                  required
                />
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Candidate and recruiter will be notified of this time window.
              </p>
            </div>
          )}

          {decisionType === "shortlisted" && (
            <div className="p-3.5 bg-emerald-50 rounded-lg border border-emerald-100 text-xs text-emerald-800">
              The staffing agency will be notified of your shortlist decision immediately.
            </div>
          )}

          {/* Action buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant={info.variant}
              size="sm"
              isLoading={isLoading}
            >
              {info.buttonText}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
