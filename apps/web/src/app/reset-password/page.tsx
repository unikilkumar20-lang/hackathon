"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Shield, KeyRound, AlertCircle, CheckCircle2, ArrowLeft } from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";

export default function ResetPasswordPage() {
  const { sendPasswordReset, isConfigured } = useAuth();
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setError(null);
    setLoading(true);
    try {
      await sendPasswordReset(email);
      setSubmitted(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to trigger password reset.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-navy-900/90 border border-navy-700/70 p-8 rounded-2xl shadow-2xl backdrop-blur">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 mx-auto flex items-center justify-center mb-4">
            <KeyRound className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Reset your Password</h1>
          <p className="text-xs text-slate-400 mt-1">
            Enter your email to receive a secure Firebase recovery link
          </p>
        </div>

        {submitted ? (
          <div className="text-center py-4">
            <div className="w-10 h-10 rounded-full bg-teal-500/20 text-teal-400 mx-auto flex items-center justify-center mb-3">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="font-semibold text-white text-sm mb-1">Check your inbox</h3>
            <p className="text-xs text-slate-300 mb-6">
              If an account exists for <span className="text-teal-300 font-mono">{email}</span>, you will receive password reset instructions shortly.
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-xs font-semibold text-teal-400 hover:text-teal-300 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Sign In</span>
            </Link>
          </div>
        ) : (
          <>
            {error && (
              <div className="mb-6 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>{error}</div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5" htmlFor="email">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading || !isConfigured}
                  placeholder="developer@example.com"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-navy-950 border border-navy-700 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:border-teal-500 transition-colors disabled:opacity-50"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading || !isConfigured}
                className="w-full py-2.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-sm shadow-md transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? "Sending..." : "Send Reset Link"}
              </button>
            </form>

            <div className="mt-6 text-center">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-3 h-3" />
                <span>Back to Sign In</span>
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
