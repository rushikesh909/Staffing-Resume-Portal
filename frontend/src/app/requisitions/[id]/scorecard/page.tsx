"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AuthGuard } from "@/components/AuthGuard";
import {
  useRequisition,
  useUpdateScorecard,
} from "@/hooks/useRequisitions";
import { ScorecardCriterionItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  ArrowLeft,
  Plus,
  Trash2,
  Save,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Sliders,
  ListFilter,
  Users,
  Kanban,
} from "lucide-react";

export default function ScorecardPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const { data: requisition, isLoading, isError, error } = useRequisition(id);
  const updateMutation = useUpdateScorecard(id);

  const [criteria, setCriteria] = useState<ScorecardCriterionItem[]>([]);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Normalize scorecard criteria on load
  useEffect(() => {
    if (!requisition?.scorecard) return;

    const raw: any = requisition.scorecard;
    let list: ScorecardCriterionItem[] = [];

    if (Array.isArray(raw) && raw.length > 0) {
      list = raw.map((c: any, idx: number) => ({
        id: c.id || `crit-${idx}`,
        name: c.name || "",
        type: c.type || "skill",
        weight: typeof c.weight === "number" ? c.weight : 1.0,
        required: Boolean(c.required),
        value: c.value ?? null,
      }));
    } else if (Array.isArray(raw?.criteria) && raw.criteria.length > 0) {
      list = raw.criteria.map((c: any, idx: number) => ({
        id: c.id || `crit-${idx}`,
        name: c.name || "",
        type: c.type || "skill",
        weight: typeof c.weight === "number" ? c.weight : 1.0,
        required: Boolean(c.required),
        value: c.value ?? null,
      }));
    } else {
      // Parse from structured keys if present
      if (Array.isArray(raw.skills)) {
        raw.skills.forEach((skill: string, idx: number) => {
          list.push({
            id: `skill-${idx}`,
            name: skill,
            type: "skill",
            weight: 1.0,
            required: true,
          });
        });
      }

      if (raw.experience_min !== undefined && raw.experience_min !== null) {
        list.push({
          id: "exp-min",
          name: `Minimum Experience (${raw.experience_min}+ yrs)`,
          type: "experience",
          weight: 1.5,
          required: true,
          value: raw.experience_min,
        });
      }

      if (raw.notice_days_max !== undefined && raw.notice_days_max !== null) {
        list.push({
          id: "notice-max",
          name: `Notice Period (<= ${raw.notice_days_max} days)`,
          type: "notice",
          weight: 1.0,
          required: false,
          value: raw.notice_days_max,
        });
      }

      if (raw.location) {
        list.push({
          id: "loc",
          name: `Location: ${raw.location}`,
          type: "location",
          weight: 0.8,
          required: false,
          value: raw.location,
        });
      }
    }

    // Default fallback if scorecard is empty
    if (list.length === 0) {
      list = [
        { id: "1", name: "Python / Backend", type: "skill", weight: 1.5, required: true },
        { id: "2", name: "Relevant Experience (3+ years)", type: "experience", weight: 1.0, required: true },
        { id: "3", name: "Database Design & SQL", type: "skill", weight: 1.0, required: false },
      ];
    }

    setCriteria(list);
  }, [requisition]);

  const handleAddCriterion = () => {
    const newItem: ScorecardCriterionItem = {
      id: `custom-${Date.now()}`,
      name: "",
      type: "custom",
      weight: 1.0,
      required: false,
    };
    setCriteria([...criteria, newItem]);
  };

  const handleRemoveCriterion = (index: number) => {
    setCriteria(criteria.filter((_, idx) => idx !== index));
  };

  const handleUpdateCriterion = (
    index: number,
    field: keyof ScorecardCriterionItem,
    value: any
  ) => {
    setCriteria((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleSave = async () => {
    setSaveSuccess(false);
    setSaveError(null);

    // Prepare payload keeping both criteria array and extracted dictionary fields
    const skills = criteria
      .filter((c) => c.type === "skill" || c.name.toLowerCase().includes("python") || c.name.toLowerCase().includes("fastapi"))
      .map((c) => c.name);

    const expCriterion = criteria.find((c) => c.type === "experience");
    const noticeCriterion = criteria.find((c) => c.type === "notice");

    const rawScorecard = requisition?.scorecard as any;
    const formattedCriteria = criteria.map((c) => ({
      name: c.name,
      type: c.type || "skill",
      weight: typeof c.weight === "number" ? c.weight : 1.0,
      required: Boolean(c.required),
    }));

    try {
      await updateMutation.mutateAsync(formattedCriteria);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      setSaveError(
        err.response?.data?.detail || err.message || "Failed to update scorecard"
      );
    }
  };

  return (
    <AuthGuard allowedRoles={["recruiter", "delivery_head"]}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
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
          <span className="text-red-600 font-medium">Scorecard</span>
        </div>

        {/* Header with Title & Action Tabs */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-900">
                  {isLoading ? <Skeleton className="h-7 w-64" /> : requisition?.title}
                </h1>
                {requisition && (
                  <Badge variant="success" size="sm">
                    {requisition.status}
                  </Badge>
                )}
              </div>
              <p className="mt-1 text-sm text-slate-500">
                AI-extracted scorecard criteria. Edit weights and requirements to calibrate candidate scoring.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Link href={`/requisitions/${id}/upload`}>
                <Button variant="primary" leftIcon={<UploadCloud className="w-4 h-4" />}>
                  Upload CVs
                </Button>
              </Link>
            </div>
          </div>

          {/* Requisition Tab Navigation */}
          <div className="flex items-center gap-1 border-t border-slate-100 mt-6 pt-3 overflow-x-auto">
            <Link
              href={`/requisitions/${id}/scorecard`}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-red-50 text-red-700 flex items-center gap-1.5"
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
              className="px-3.5 py-2 text-xs font-medium rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-1.5"
            >
              <Kanban className="w-3.5 h-3.5" />
              <span>Pipeline View</span>
            </Link>
          </div>
        </div>

        {/* Scorecard Editor Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-red-600" />
                <span>Evaluation Criteria ({criteria.length})</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Weights scale from 0.1 (low relevance) to 3.0 (critical factor).
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleAddCriterion}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Add Criterion
            </Button>
          </div>

          {/* Feedback states */}
          {saveSuccess && (
            <div className="mt-4 p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center gap-2.5 text-xs text-emerald-800 font-medium">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Scorecard saved successfully. Candidate ranking will reflect these weights.</span>
            </div>
          )}

          {saveError && (
            <div className="mt-4 p-3.5 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2.5 text-xs text-red-800 font-medium">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span>Failed to save: {saveError}</span>
            </div>
          )}

          {/* Criteria List */}
          <div className="mt-6 space-y-4">
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((n) => (
                  <Skeleton key={n} className="h-16 w-full" />
                ))}
              </div>
            ) : (
              criteria.map((item, index) => (
                <div
                  key={item.id || index}
                  className="p-4 rounded-lg border border-slate-200 hover:border-slate-300 bg-white transition-colors flex flex-col md:flex-row md:items-center gap-4"
                >
                  {/* Name input */}
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                      Criterion / Skill Name
                    </label>
                    <input
                      type="text"
                      value={item.name}
                      onChange={(e) =>
                        handleUpdateCriterion(index, "name", e.target.value)
                      }
                      placeholder="e.g. FastApi, PostgreSQL, Microservices"
                      className="w-full px-3 py-1.5 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-800"
                    />
                  </div>

                  {/* Type selector */}
                  <div className="w-full md:w-36">
                    <label className="block text-xs font-medium text-slate-500 mb-1">
                      Type
                    </label>
                    <select
                      value={item.type}
                      onChange={(e) =>
                        handleUpdateCriterion(index, "type", e.target.value)
                      }
                      className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700"
                    >
                      <option value="skill">Skill</option>
                      <option value="experience">Experience</option>
                      <option value="notice">Notice Period</option>
                      <option value="location">Location</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>

                  {/* Weight Slider & Value */}
                  <div className="w-full md:w-44">
                    <div className="flex justify-between items-center text-xs font-medium text-slate-500 mb-1">
                      <span>Weight</span>
                      <span className="font-semibold text-blue-600">
                        {item.weight.toFixed(1)}x
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0.1"
                      max="3.0"
                      step="0.1"
                      value={item.weight}
                      onChange={(e) =>
                        handleUpdateCriterion(
                          index,
                          "weight",
                          parseFloat(e.target.value)
                        )
                      }
                      className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                    />
                  </div>

                  {/* Required Toggle */}
                  <div className="flex items-center gap-2 pt-2 md:pt-4">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={item.required}
                        onChange={(e) =>
                          handleUpdateCriterion(index, "required", e.target.checked)
                        }
                        className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                      />
                      <span className="text-xs font-medium text-slate-700">
                        Mandatory
                      </span>
                    </label>
                  </div>

                  {/* Delete button */}
                  <div className="pt-2 md:pt-4">
                    <button
                      type="button"
                      onClick={() => handleRemoveCriterion(index)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Remove criterion"
                      aria-label="Remove criterion"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Action buttons footer */}
          <div className="mt-8 pt-5 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
            <Link href={`/requisitions/${id}/upload`}>
              <Button
                variant="outline"
                size="md"
                leftIcon={<UploadCloud className="w-4 h-4" />}
              >
                Proceed to Upload CVs
              </Button>
            </Link>

            <Button
              variant="primary"
              size="md"
              onClick={handleSave}
              isLoading={updateMutation.isPending}
              leftIcon={<Save className="w-4 h-4" />}
            >
              Save Scorecard Criteria
            </Button>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
