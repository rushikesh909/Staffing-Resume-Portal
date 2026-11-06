"use client";

import React, { useRef, useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2, Sparkles, X } from "lucide-react";
import { FileUploadItem } from "@/lib/types";
import { Badge } from "./ui/Badge";

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFilesSelected,
  disabled = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const validFiles = Array.from(e.dataTransfer.files).filter((file) =>
        isValidFileType(file)
      );
      if (validFiles.length > 0) {
        onFilesSelected(validFiles);
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files).filter((file) =>
        isValidFileType(file)
      );
      if (files.length > 0) {
        onFilesSelected(files);
      }
      e.target.value = "";
    }
  };

  const isValidFileType = (file: File) => {
    const validExtensions = [".pdf", ".docx", ".doc", ".txt"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    return validExtensions.includes(ext);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
        disabled
          ? "opacity-50 cursor-not-allowed border-slate-200 bg-slate-50"
          : isDragOver
          ? "border-red-500 bg-red-50/40"
          : "border-slate-300 hover:border-red-400 bg-slate-50/50 hover:bg-slate-50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.doc,.txt"
        className="hidden"
        onChange={handleInputChange}
        disabled={disabled}
      />
      <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-4">
        <UploadCloud className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-800">
        Drag and drop resumes here, or browse
      </h3>
      <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
        Supports PDF, DOCX, and TXT files. Upload multiple resumes simultaneously for batch parsing and AI rubric scoring.
      </p>
      <div className="mt-4 inline-flex items-center gap-2 text-xs font-medium text-red-700 bg-red-50 px-3 py-1 rounded-full border border-red-100">
        <Sparkles className="w-3.5 h-3.5" />
        <span>Instant OCR + AI Criteria Matching</span>
      </div>
    </div>
  );
};

export const FileStatusRow: React.FC<{
  item: FileUploadItem;
  onRemove?: () => void;
}> = ({ item, onRemove }) => {
  const getStatusBadge = () => {
    switch (item.status) {
      case "queued":
        return <Badge variant="neutral" size="sm">Queued</Badge>;
      case "uploading":
        return (
          <span className="inline-flex items-center gap-1.5 text-xs text-red-600 font-medium">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Uploading ({item.progress}%)
          </span>
        );
      case "parsed":
        return (
          <span className="inline-flex items-center gap-1.5 text-xs text-amber-600 font-medium">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Parsing CV...
          </span>
        );
      case "scored":
        return (
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {item.score !== undefined ? `Scored (${Math.round(item.score)}/100)` : "Scored"}
          </span>
        );
      case "duplicate":
        return (
          <Badge variant="warning" size="sm">
            Duplicate Detected
          </Badge>
        );
      case "error":
        return (
          <Badge variant="danger" size="sm">
            Failed
          </Badge>
        );
      default:
        return null;
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-3.5 bg-white rounded-lg border border-slate-200 flex items-center justify-between gap-3 text-sm">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500 flex-shrink-0">
          <FileText className="w-4 h-4" />
        </div>
        <div className="min-w-0">
          <p className="font-medium text-slate-800 text-xs sm:text-sm truncate">
            {item.name}
          </p>
          <p className="text-[11px] text-slate-400">
            {formatSize(item.size)}
            {item.error && (
              <span className="text-red-500 ml-2 font-medium">
                • {item.error}
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        {getStatusBadge()}
        {onRemove && item.status === "queued" && (
          <button
            type="button"
            onClick={onRemove}
            className="text-slate-400 hover:text-slate-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
