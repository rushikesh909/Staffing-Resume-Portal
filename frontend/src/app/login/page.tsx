"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { AlertCircle, Lock, Mail } from "lucide-react";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const [authError, setAuthError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setAuthError(null);
    setSubmitting(true);
    try {
      await login(data);
    } catch (err: any) {
      setAuthError(err.message || "Invalid email or password");
    } finally {
      setSubmitting(false);
    }
  };

  const fillQuickDemo = (email: string) => {
    setValue("email", email);
    setValue("password", "password123");
    setAuthError(null);
  };

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <div className="mx-auto w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white text-xl font-bold shadow-sm">
            S
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">
            Sign in to StaffingAI
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Screening & Client Collaboration Platform
          </p>
        </div>

        <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
          {authError && (
            <div className="mb-5 p-3.5 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-700">
                <span className="font-medium">Authentication failed: </span>
                {authError}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Input
                label="Work Email"
                type="email"
                placeholder="recruiter@staffing.com"
                autoComplete="email"
                error={errors.email?.message}
                {...register("email")}
              />
            </div>

            <div>
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                error={errors.password?.message}
                {...register("password")}
              />
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={submitting}
                className="w-full"
              >
                Sign In
              </Button>
            </div>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2.5 text-center">
              Quick Fill Demo Accounts
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => fillQuickDemo("recruiter@staffing.com")}
                className="text-xs text-left p-2 rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 transition-colors"
              >
                <div className="font-medium text-slate-800">Recruiter</div>
                <div className="text-[11px] text-slate-500 truncate">
                  recruiter@staffing.com
                </div>
              </button>

              <button
                type="button"
                onClick={() => fillQuickDemo("hiring@client.com")}
                className="text-xs text-left p-2 rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 transition-colors"
              >
                <div className="font-medium text-slate-800">Client Manager</div>
                <div className="text-[11px] text-slate-500 truncate">
                  hiring@client.com
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
