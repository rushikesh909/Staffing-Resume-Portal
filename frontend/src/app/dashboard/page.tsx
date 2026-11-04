"use client";

import React from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/AuthGuard";
import { useRequisitions, useClients } from "@/hooks/useRequisitions";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  Briefcase,
  FileCheck,
  Users,
  PlusCircle,
  ExternalLink,
  ChevronRight,
  UploadCloud,
  ListFilter,
  BarChart3,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";

export default function DashboardPage() {
  const { data: requisitions, isLoading, isError, error, refetch } = useRequisitions();
  const { data: clients } = useClients();

  const clientMap = React.useMemo(() => {
    const map = new Map<number, string>();
    clients?.forEach((c) => map.set(c.id, c.name));
    return map;
  }, [clients]);

  // Derived metrics
  const totalRequisitions = requisitions?.length || 0;
  const totalCandidates = requisitions?.reduce(
    (sum, req) => sum + (req.candidates_count || 0),
    0
  ) || 0;
  const activeRequisitions =
    requisitions?.filter((r) => r.status === "active").length || 0;

  return (
    <AuthGuard allowedRoles={["recruiter"]}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Recruiter Dashboard
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Manage requisitions, AI scorecards, and candidate pipelines.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/requisitions/new">
              <Button leftIcon={<PlusCircle className="w-4 h-4" />}>
                New Requisition
              </Button>
            </Link>
          </div>
        </div>

        {/* Metrics Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mt-6">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">
                Open Requisitions
              </span>
              <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <Briefcase className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <div className="text-3xl font-bold text-slate-900">
                  {activeRequisitions}
                </div>
              )}
              <p className="text-xs text-slate-400 mt-1">
                {totalRequisitions} total requisitions tracked
              </p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">
                CVs Processed
              </span>
              <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <FileCheck className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <div className="text-3xl font-bold text-slate-900">
                  {totalCandidates}
                </div>
              )}
              <p className="text-xs text-slate-400 mt-1">
                Parsed and scored against criteria
              </p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">
                Active in Pipeline
              </span>
              <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Users className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <div className="text-3xl font-bold text-slate-900">
                  {totalCandidates}
                </div>
              )}
              <p className="text-xs text-slate-400 mt-1">
                Across all candidate stages
              </p>
            </div>
          </div>
        </div>

        {/* Requisitions Section */}
        <div className="mt-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">
              Active Requisitions
            </h2>
            <span className="text-xs text-slate-500 font-medium">
              {requisitions?.length || 0} requisitions
            </span>
          </div>

          {/* Loading state */}
          {isLoading && (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div
                  key={n}
                  className="bg-white p-5 rounded-xl border border-slate-200 flex items-center justify-between"
                >
                  <div className="space-y-2 w-1/2">
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-4 w-1/3" />
                  </div>
                  <Skeleton className="h-8 w-24" />
                </div>
              ))}
            </div>
          )}

          {/* Error state */}
          {isError && (
            <div className="bg-white p-8 rounded-xl border border-red-200 text-center">
              <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-slate-900">
                Failed to load requisitions
              </h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">
                {(error as any)?.message || "Could not retrieve requisitions from the server."}
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

          {/* Empty state */}
          {!isLoading && !isError && (!requisitions || requisitions.length === 0) && (
            <EmptyState
              title="No requisitions yet"
              description="Get started by creating your first job requisition. The AI will automatically extract a scoring rubric."
              icon={<Briefcase className="w-6 h-6 text-blue-600" />}
              action={
                <Link href="/requisitions/new">
                  <Button leftIcon={<PlusCircle className="w-4 h-4" />}>
                    Create Requisition
                  </Button>
                </Link>
              }
            />
          )}

          {/* Requisitions List */}
          {!isLoading && !isError && requisitions && requisitions.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
              {requisitions.map((req) => {
                const clientName = clientMap.get(req.client_id) || req.client_name || `Client #${req.client_id}`;
                const formattedDate = new Date(req.created_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                });

                return (
                  <div
                    key={req.id}
                    className="p-5 hover:bg-slate-50/70 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <Link
                          href={`/requisitions/${req.id}/candidates`}
                          className="font-semibold text-slate-900 hover:text-blue-600 transition-colors text-base truncate"
                        >
                          {req.title}
                        </Link>
                        <Badge
                          variant={req.status === "active" ? "success" : "default"}
                          size="sm"
                        >
                          {req.status}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500">
                        <span className="font-medium text-slate-700">
                          {clientName}
                        </span>
                        <span>•</span>
                        <span>Created {formattedDate}</span>
                        <span>•</span>
                        <span>
                          {req.candidates_count !== undefined
                            ? `${req.candidates_count} candidates`
                            : "Candidate pipeline ready"}
                        </span>
                      </div>
                    </div>

                    {/* Quick Action Links */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <Link href={`/requisitions/${req.id}/scorecard`}>
                        <Button variant="outline" size="sm" leftIcon={<ListFilter className="w-3.5 h-3.5" />}>
                          Scorecard
                        </Button>
                      </Link>

                      <Link href={`/requisitions/${req.id}/upload`}>
                        <Button variant="outline" size="sm" leftIcon={<UploadCloud className="w-3.5 h-3.5" />}>
                          Upload CVs
                        </Button>
                      </Link>

                      <Link href={`/requisitions/${req.id}/candidates`}>
                        <Button variant="outline" size="sm" leftIcon={<Users className="w-3.5 h-3.5" />}>
                          Ranked List
                        </Button>
                      </Link>

                      <Link href={`/requisitions/${req.id}/pipeline`}>
                        <Button variant="ghost" size="sm" rightIcon={<ChevronRight className="w-3.5 h-3.5" />}>
                          Pipeline
                        </Button>
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
