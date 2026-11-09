"use client";

import React, { useState, useRef, useEffect } from "react";
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
  ChevronDown,
  Building,
  ShieldCheck,
} from "lucide-react";

export const NavBar: React.FC = () => {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const profileDropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        profileDropdownRef.current &&
        !profileDropdownRef.current.contains(event.target as Node)
      ) {
        setProfileDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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

  const getRoleLabel = () => {
    if (isDeliveryHead) return "Delivery Head";
    if (isRecruiter) return "Senior Recruiter";
    return "Client Hiring Manager";
  };

  const getOrgLabel = () => {
    if (isInternal) return "TalentBridge Staffing (Internal)";
    if (user.email.includes("techcorp")) return "TechCorp Solutions";
    if (user.email.includes("finserv")) return "FinServ India";
    return "Client Organization";
  };

  const displayName =
    user.full_name ||
    user.email.split("@")[0].replace(/[._]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  const userInitial = displayName.charAt(0).toUpperCase() || "U";

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Main Nav */}
          <div className="flex items-center gap-6 lg:gap-8">
            <Link
              href={isInternal ? "/dashboard" : "/client/portal"}
              className="flex items-center gap-2.5 font-bold text-slate-900 tracking-tight text-lg group"
            >
              <div className="w-8 h-8 rounded-lg bg-red-600 flex items-center justify-center text-white font-bold shadow-sm group-hover:bg-red-700 transition-colors">
                S
              </div>
              <span className="font-semibold text-slate-900">
                Staffing<span className="text-red-600">AI</span>
              </span>
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
                        ? "bg-red-50 text-red-700 font-semibold"
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

          {/* Right side: Profile Section & Quick Actions */}
          <div className="flex items-center gap-3">
            {/* User Profile Dropdown Pill */}
            <div className="relative" ref={profileDropdownRef}>
              <button
                type="button"
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all text-left focus:outline-none focus:ring-2 focus:ring-red-500/20"
                aria-expanded={profileDropdownOpen}
                aria-haspopup="true"
                id="user-profile-menu-button"
              >
                <div className="relative">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-red-600 to-rose-400 text-white font-semibold flex items-center justify-center text-sm shadow-sm">
                    {userInitial}
                  </div>
                  <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 border-2 border-white rounded-full"></span>
                </div>

                <div className="hidden sm:block leading-tight">
                  <div className="text-xs font-semibold text-slate-900 max-w-[130px] truncate">
                    {displayName}
                  </div>
                  <div className="text-[11px] text-slate-500 font-medium">
                    {getRoleLabel()}
                  </div>
                </div>

                <ChevronDown
                  className={`w-3.5 h-3.5 text-slate-400 transition-transform ${
                    profileDropdownOpen ? "rotate-180" : ""
                  }`}
                />
              </button>

              {/* Profile Dropdown Menu */}
              {profileDropdownOpen && (
                <div
                  className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-xl border border-slate-100 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150"
                  role="menu"
                  aria-orientation="vertical"
                  aria-labelledby="user-profile-menu-button"
                >
                  {/* User Details Header */}
                  <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50">
                    <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">
                      Signed in as
                    </p>
                    <p className="text-sm font-semibold text-slate-900 mt-0.5 truncate">
                      {displayName}
                    </p>
                    <p className="text-xs text-slate-600 truncate">{user.email}</p>

                    <div className="mt-2.5 flex items-center gap-1.5 flex-wrap">
                      <Badge
                        variant={
                          isDeliveryHead
                            ? "warning"
                            : isRecruiter
                            ? "info"
                            : "success"
                        }
                        size="sm"
                      >
                        <ShieldCheck className="w-3 h-3 mr-1 inline" />
                        {getRoleLabel()}
                      </Badge>
                    </div>

                    <div className="mt-1.5 flex items-center gap-1 text-[11px] text-slate-500">
                      <Building className="w-3 h-3 text-slate-400" />
                      <span className="truncate">{getOrgLabel()}</span>
                    </div>
                  </div>

                  {/* Menu Items */}
                  <div className="py-1">
                    {isInternal ? (
                      <>
                        <Link
                          href="/dashboard"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                        >
                          <Layers className="w-4 h-4 text-slate-400" />
                          <span>Recruiter Dashboard</span>
                        </Link>
                        <Link
                          href="/requisitions/new"
                          onClick={() => setProfileDropdownOpen(false)}
                          className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                        >
                          <PlusCircle className="w-4 h-4 text-slate-400" />
                          <span>Create Requisition</span>
                        </Link>
                      </>
                    ) : (
                      <Link
                        href="/client/portal"
                        onClick={() => setProfileDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                      >
                        <Briefcase className="w-4 h-4 text-slate-400" />
                        <span>Client Review Portal</span>
                      </Link>
                    )}
                  </div>

                  {/* Logout Button */}
                  <div className="pt-1 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm font-medium text-rose-600 hover:bg-rose-50 hover:text-rose-700 transition-colors text-left"
                    >
                      <LogOut className="w-4 h-4 text-rose-500" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Desktop Direct Sign Out Button */}
            <div className="hidden lg:block">
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                leftIcon={<LogOut className="w-3.5 h-3.5 text-slate-500" />}
                className="text-slate-700 hover:text-rose-600 hover:border-rose-300"
              >
                Sign Out
              </Button>
            </div>

            {/* Mobile menu hamburger button */}
            <div className="flex items-center md:hidden">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
                aria-label="Toggle navigation menu"
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6 text-slate-700" />
                ) : (
                  <Menu className="w-6 h-6 text-slate-700" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-4 space-y-3 animate-in fade-in duration-100">
          {/* User profile card in mobile drawer */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-600 text-white font-semibold flex items-center justify-center text-sm shadow-sm">
                {userInitial}
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-900">
                  {displayName}
                </div>
                <div className="text-xs text-slate-500 truncate max-w-[180px]">
                  {user.email}
                </div>
                <div className="mt-1">
                  <Badge
                    variant={
                      isDeliveryHead
                        ? "warning"
                        : isRecruiter
                        ? "info"
                        : "success"
                    }
                    size="sm"
                  >
                    {getRoleLabel()}
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Links in mobile drawer */}
          <div className="space-y-1">
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
                      ? "bg-red-50 text-red-700 font-semibold"
                      : "text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile Sign Out */}
          <div className="pt-2 border-t border-slate-100">
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-center text-rose-600 hover:bg-rose-50 hover:border-rose-300"
              onClick={() => {
                setMobileMenuOpen(false);
                logout();
              }}
              leftIcon={<LogOut className="w-4 h-4 text-rose-600" />}
            >
              Sign Out
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
};
