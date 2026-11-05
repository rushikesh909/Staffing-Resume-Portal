"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AuthGuard } from "@/components/AuthGuard";
import { useClients, useCreateRequisition } from "@/hooks/useRequisitions";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { ArrowLeft, Sparkles, AlertCircle, Building2 } from "lucide-react";

const requisitionSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters"),
  client_id: z.union([z.string().min(1, "Please select a client"), z.number().min(1, "Please select a client")]),
  jd_text: z.string().min(20, "Job description should be at least 20 characters"),
});

type RequisitionFormData = z.infer<typeof requisitionSchema>;

const SAMPLE_JD = `Role: Senior Backend Engineer (Python / FastAPI)
Experience: 4-7 years
Location: Remote / Hybrid (New York, NY)
Notice Period: Immediate to 30 days max
Salary: $140,000 - $180,000

Responsibilities:
- Build high-performance REST APIs and microservices using Python and FastAPI
- Design relational schemas in PostgreSQL and manage migrations with Alembic
- Implement caching with Redis and async worker queues with Celery / RQ
- Collaborate with frontend engineers using Next.js and Tailwind CSS
- Write comprehensive unit tests and automated test suites

Requirements:
- Strong experience with Python 3.10+, FastAPI, and SQLAlchemy
- Solid grasp of SQL, query optimization, and transaction management
- Familiarity with Docker, Kubernetes, and AWS deployment pipelines
- Proven ability to deliver production-grade services in an agile environment`;

export default function NewRequisitionPage() {
  const router = useRouter();
  const { data: clients, isLoading: clientsLoading } = useClients();
  const createMutation = useCreateRequisition();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RequisitionFormData>({
    resolver: zodResolver(requisitionSchema),
    defaultValues: {
      title: "",
      client_id: 0,
      jd_text: "",
    },
  });

  const onSubmit = async (data: RequisitionFormData) => {
    setSubmitError(null);
    try {
      const created = await createMutation.mutateAsync(data);
      router.push(`/requisitions/${created.id}/scorecard`);
    } catch (err: any) {
      setSubmitError(
        err.response?.data?.detail || err.message || "Failed to create requisition"
      );
    }
  };

  const handleFillSample = () => {
    setValue("title", "Senior Backend Engineer (Python / FastAPI)");
    if (clients && clients.length > 0) {
      setValue("client_id", clients[0].id);
    }
    setValue("jd_text", SAMPLE_JD);
  };

  return (
    <AuthGuard allowedRoles={["recruiter", "delivery_head"]}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Back navigation */}
        <div className="mb-6">
          <Link
            href="/dashboard"
            className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors gap-1.5"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </Link>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-100">
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">
                Create New Requisition
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Paste the job description. StaffingAI will automatically extract the candidate scorecard criteria.
              </p>
            </div>
            <button
              type="button"
              onClick={handleFillSample}
              className="text-xs font-medium text-blue-600 hover:text-blue-800 underline flex items-center gap-1 self-start sm:self-auto"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Fill with sample JD
            </button>
          </div>

          {submitError && (
            <div className="mt-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-700">
                <span className="font-medium">Error: </span>
                {submitError}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 mt-6">
            {/* Title */}
            <div>
              <Input
                label="Requisition Title"
                placeholder="e.g. Senior Backend Engineer"
                error={errors.title?.message}
                {...register("title")}
              />
            </div>

            {/* Client selector */}
            <div>
              <label
                htmlFor="client_id"
                className="block text-sm font-medium text-slate-700 mb-1"
              >
                Client Organization
              </label>
              <div className="relative">
                <select
                  id="client_id"
                  className={`w-full px-3 py-2 text-sm bg-white border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-50 ${
                    errors.client_id ? "border-red-400" : "border-slate-300"
                  }`}
                  {...register("client_id")}
                  disabled={clientsLoading}
                >
                  <option value={0}>Select a client...</option>
                  {clients?.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name} ({client.contact_email})
                    </option>
                  ))}
                  {(!clients || clients.length === 0) && (
                    <option value={1}>Acme Corporation (Demo Client)</option>
                  )}
                </select>
              </div>
              {errors.client_id && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.client_id.message}
                </p>
              )}
            </div>

            {/* JD Text */}
            <div>
              <Textarea
                label="Job Description (Raw Text)"
                rows={12}
                placeholder="Paste the full job description text here..."
                error={errors.jd_text?.message}
                helperText="Include mandatory skills, years of experience, locations, and qualifications for best scorecard extraction."
                {...register("jd_text")}
              />
            </div>

            {/* Submit */}
            <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-100">
              <Link href="/dashboard">
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </Link>
              <Button
                type="submit"
                variant="primary"
                isLoading={createMutation.isPending}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                {createMutation.isPending
                  ? "Extracting Scorecard with AI..."
                  : "Create & Extract Scorecard"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </AuthGuard>
  );
}
