"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import {
  Briefcase,
  Layers,
  PlusCircle,
  LogOut,
  Menu,
  X,
  User as UserIcon,
} from "lucide-react";

export const NavBar: React.FC = () => {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (!user) return null;

  const isRecruiter = user.role === "recruiter";
  const isDeliveryHead = user.role === "delivery_head";
  const isInternal = isRecruiter || isDeliveryHead;

  const internalNav = [
    { label: "Dashboard", href: "/dashboard", icon: Layers },
    { label: "New Requisition", href: "/requisitions/new", icon: PlusCircle },
  ];

  const clientNav = [
    { label: "Candidate Review", href: "/client/portal", icon: Briefcase },
  ];

  const navLinks = isInternal ? internalNav : clientNav;

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo & Main Nav */}
          <div className="flex items-center gap-8">
            <Link
              href={isInternal ? "/dashboard" : "/client/portal"}
              className="flex items-center gap-2 font-bold text-slate-900 tracking-tight text-lg"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-semibold">
                S
              </div>
              <span>Staffing<span className="text-blue-600">AI</span></span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-1">
              {navLinks.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors gap-2 ${
                      active
                        ? "bg-blue-50 text-blue-700"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Right side: User Profile & Logout */}
          <div className="hidden md:flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-slate-800 leading-tight">
                  {user.email}
                </div>
                <div className="mt-0.5">
                  <Badge
                    variant={
                      isDeliveryHead ? "warning" : isRecruiter ? "info" : "success"
                    }
                    size="sm"
                  >
                    {isDeliveryHead
                      ? "Delivery Head"
                      : isRecruiter
                      ? "Recruiter"
                      : "Client"}
                  </Badge>
                </div>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              leftIcon={<LogOut className="w-3.5 h-3.5" />}
            >
              Sign Out
            </Button>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-4 space-y-2">
          <div className="py-2 border-b border-slate-100 mb-2">
            <div className="text-sm font-medium text-slate-800">{user.email}</div>
            <div className="mt-1">
              <Badge
                variant={
                  isDeliveryHead ? "warning" : isRecruiter ? "info" : "success"
                }
                size="sm"
              >
                {isDeliveryHead
                  ? "Delivery Head"
                  : isRecruiter
                  ? "Recruiter"
                  : "Client Portal"}
              </Badge>
            </div>
          </div>

          {navLinks.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium ${
                  active
                    ? "bg-blue-50 text-blue-700"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <div className="pt-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-center"
              onClick={() => {
                setMobileMenuOpen(false);
                logout();
              }}
              leftIcon={<LogOut className="w-4 h-4" />}
            >
              Sign Out
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
};
