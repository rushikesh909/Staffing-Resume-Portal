import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info" | "neutral";
  size?: "sm" | "md";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  size = "md",
  className = "",
}) => {
  const variantStyles = {
    default: "bg-slate-100 text-slate-700 border-slate-200",
    neutral: "bg-slate-100 text-slate-600 border-slate-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
    info: "bg-red-50 text-red-700 border-red-200",
  };

  const sizeStyles = {
    sm: "text-[11px] px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
  };

  return (
    <span
      className={`inline-flex items-center font-medium border rounded-full ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};

export const ScoreBadge: React.FC<{ score?: number | null; size?: "sm" | "md" | "lg" }> = ({
  score,
  size = "md",
}) => {
  if (score === undefined || score === null) {
    return (
      <span className="inline-flex items-center font-medium text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 border border-slate-200">
        N/A
      </span>
    );
  }

  const roundedScore = Math.round(score);
  let colorStyles = "bg-rose-50 text-rose-700 border-rose-200";
  if (roundedScore >= 70) {
    colorStyles = "bg-emerald-50 text-emerald-700 border-emerald-200";
  } else if (roundedScore >= 40) {
    colorStyles = "bg-amber-50 text-amber-700 border-amber-200";
  }

  const sizeStyles = {
    sm: "text-xs px-2 py-0.5 font-semibold",
    md: "text-xs px-2.5 py-1 font-semibold",
    lg: "text-sm px-3 py-1 font-bold",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border ${colorStyles} ${sizeStyles[size]}`}
    >
      <span>{roundedScore}</span>
      <span className="text-[10px] font-normal opacity-70">/ 100</span>
    </span>
  );
};
