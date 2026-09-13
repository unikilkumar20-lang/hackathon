"use client";

import React from "react";
import Link from "next/link";
import { Shield, Sparkles, FolderGit2, LogIn, LogOut, AlertCircle } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";

export const Header: React.FC = () => {
  const { user, loading, isConfigured, logout } = useAuth();

  return (
    <header className="border-b border-navy-700/60 bg-navy-900/80 backdrop-blur sticky top-0 z-50">
      {!isConfigured && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-xs text-amber-300 flex items-center justify-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Firebase Authentication credentials are not configured yet in <code className="bg-navy-950 px-1 py-0.5 rounded text-teal-300">apps/web/.env.local</code>. Check <code className="bg-navy-950 px-1 py-0.5 rounded">docs/FIREBASE_SETUP.md</code>.
          </span>
        </div>
      )}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 group-hover:border-teal-400/60 transition-colors">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white group-hover:text-teal-300 transition-colors">
                RippleGuard
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs text-slate-400 font-normal">
                Explainable Dependency Risk
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            <Link
              href="/demo"
              className="text-slate-300 hover:text-teal-400 transition-colors flex items-center gap-1.5"
            >
              <Sparkles className="w-4 h-4 text-teal-400" />
              <span>Synthetic Demo</span>
            </Link>
            <Link
              href="/dashboard"
              className="text-slate-300 hover:text-teal-400 transition-colors flex items-center gap-1.5"
            >
              <FolderGit2 className="w-4 h-4 text-slate-400" />
              <span>Projects</span>
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {loading ? (
            <div className="w-20 h-8 bg-navy-800 animate-pulse rounded-md" />
          ) : user ? (
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-medium text-slate-200">
                  {user.displayName || user.email?.split("@")[0] || "Authenticated"}
                </div>
                <div className="text-[10px] text-slate-400">{user.email}</div>
              </div>
              <button
                onClick={() => logout()}
                className="p-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 hover:text-white transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-200 hover:text-white bg-navy-800 hover:bg-navy-700 border border-navy-700 transition-colors flex items-center gap-1.5"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
              <Link
                href="/signup"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-navy-950 bg-teal-400 hover:bg-teal-300 transition-colors"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
