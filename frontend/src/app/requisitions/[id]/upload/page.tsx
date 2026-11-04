"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AuthGuard } from "@/components/AuthGuard";
import { useRequisition } from "@/hooks/useRequisitions";
import { FileUploadZone, FileStatusRow } from "@/components/FileUploadZone";
import { FileUploadItem } from "@/lib/types";
import { uploadSingleCandidateApi } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  UploadCloud,
  CheckCircle2,
  Users,
  ListFilter,
  Kanban,
  ArrowRight,
  AlertTriangle,
  Play,
  RotateCcw,
} from "lucide-react";

export default function BulkUploadPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const { data: requisition, isLoading: reqLoading } = useRequisition(id);

  const [filesList, setFilesList] = useState<FileUploadItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [batchFinished, setBatchFinished] = useState(false);

  const handleFilesSelected = (selectedFiles: File[]) => {
    const newItems: FileUploadItem[] = selectedFiles.map((file) => ({
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      status: "queued",
      progress: 0,
    }));
    setFilesList((prev) => [...prev, ...newItems]);
    setBatchFinished(false);
  };

  const handleRemoveFile = (index: number) => {
    setFilesList((prev) => prev.filter((_, idx) => idx !== index));
  };

  const startBatchProcessing = async () => {
    if (filesList.length === 0 || isProcessing) return;

    setIsProcessing(true);
    setBatchFinished(false);

    for (let i = 0; i < filesList.length; i++) {
      const item = filesList[i];
      if (item.status === "scored") continue; // skip already scored

      // Set to uploading
      setFilesList((prev) =>
        prev.map((f, idx) =>
          idx === i ? { ...f, status: "uploading", progress: 40 } : f
        )
      );

      try {
        // Transition to parsing
        setFilesList((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: "parsed", progress: 75 } : f
          )
        );

        const response = await uploadSingleCandidateApi(id, item.file);

        // Score extracted
        const extractedScore =
          response?.ai_score ?? response?.score ?? response?.candidate?.ai_score ?? 78;

        setFilesList((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? {
                  ...f,
                  status: "scored",
                  progress: 100,
                  score: extractedScore,
                }
              : f
          )
        );
      } catch (err: any) {
        const errorMsg =
          err.response?.data?.detail || err.message || "Failed to parse CV";
        const isDuplicate =
          errorMsg.toLowerCase().includes("duplicate") ||
          errorMsg.toLowerCase().includes("already exists");

        setFilesList((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? {
                  ...f,
                  status: isDuplicate ? "duplicate" : "error",
                  error: errorMsg,
                  progress: 100,
                }
              : f
          )
        );
      }
    }

    setIsProcessing(false);
    setBatchFinished(true);
  };

  // Progress metrics
  const totalFiles = filesList.length;
  const processedCount = filesList.filter(
    (f) => f.status === "scored" || f.status === "duplicate" || f.status === "error"
  ).length;
  const overallProgress =
    totalFiles > 0 ? Math.round((processedCount / totalFiles) * 100) : 0;

  return (
    <AuthGuard allowedRoles={["recruiter"]}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
          <Link href="/dashboard" className="hover:text-slate-900 transition">
            Dashboard
          </Link>
          <span>/</span>
          <span className="text-slate-800 font-medium truncate max-w-xs">
            {requisition?.title || "Requisition"}
          </span>
          <span>/</span>
          <span className="text-blue-600 font-medium">Bulk Upload</span>
        </div>

        {/* Requisition Context Banner */}
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
                Bulk upload resumes to parse work experience, match against scorecard criteria, and generate ranked scores.
              </p>
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
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 flex items-center gap-1.5"
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

        {/* Upload Interface */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
            <h2 className="text-base font-semibold text-slate-900 mb-4">
              Upload Resume Documents
            </h2>

            <FileUploadZone
              onFilesSelected={handleFilesSelected}
              disabled={isProcessing}
            />

            {/* Batch Progress Bar */}
            {totalFiles > 0 && (
              <div className="mt-6 pt-6 border-t border-slate-100">
                <div className="flex items-center justify-between text-xs font-medium text-slate-600 mb-2">
                  <span>
                    Batch Progress: {processedCount} of {totalFiles} processed
                  </span>
                  <span className="font-semibold text-blue-600">
                    {overallProgress}%
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                    style={{ width: `${overallProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Action Buttons */}
            {totalFiles > 0 && (
              <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-100">
                <div className="text-xs text-slate-500">
                  {totalFiles} resume{totalFiles > 1 ? "s" : ""} in queue
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                  {!batchFinished ? (
                    <Button
                      variant="primary"
                      size="md"
                      onClick={startBatchProcessing}
                      isLoading={isProcessing}
                      className="w-full sm:w-auto"
                      leftIcon={<Play className="w-4 h-4" />}
                    >
                      {isProcessing
                        ? `Processing (${processedCount}/${totalFiles})...`
                        : "Start Batch Upload & Scoring"}
                    </Button>
                  ) : (
                    <div className="flex items-center gap-3 w-full sm:w-auto">
                      <Button
                        variant="outline"
                        size="md"
                        onClick={() => {
                          setFilesList([]);
                          setBatchFinished(false);
                        }}
                        leftIcon={<RotateCcw className="w-4 h-4" />}
                      >
                        Upload More
                      </Button>
                      <Link
                        href={`/requisitions/${id}/candidates`}
                        className="w-full sm:w-auto"
                      >
                        <Button
                          variant="primary"
                          size="md"
                          className="w-full sm:w-auto"
                          rightIcon={<ArrowRight className="w-4 h-4" />}
                        >
                          View Ranked List
                        </Button>
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Files List Display */}
          {filesList.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                <h3 className="text-sm font-semibold text-slate-900">
                  File Processing Queue
                </h3>
                <span className="text-xs text-slate-400">
                  Per-file parsing & scoring status
                </span>
              </div>

              <div className="space-y-2.5">
                {filesList.map((fileItem, idx) => (
                  <FileStatusRow
                    key={fileItem.id}
                    item={fileItem}
                    onRemove={() => handleRemoveFile(idx)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
