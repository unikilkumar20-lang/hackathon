"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  FolderGit2,
  Plus,
  Layers,
  Calendar,
  AlertCircle,
  ArrowRight,
  Shield,
  RefreshCw,
  Server,
} from "lucide-react";
import { useAuth } from "@/features/auth/AuthContext";
import { apiClient, ApiError } from "@/lib/api-client";
import { Project, PaginatedResponse } from "@/lib/types";

export default function DashboardPage() {
  const { user, loading: authLoading, isConfigured } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // New project modal state
  const [showModal, setShowModal] = useState<boolean>(false);
  const [name, setName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [creating, setCreating] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient<PaginatedResponse<Project>>("/projects");
      setProjects(response.items);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`${err.code}: ${err.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load projects.");
      }
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!authLoading && user) {
      fetchProjects();
    } else if (!authLoading && !user) {
      setLoading(false);
    }
  }, [authLoading, user, fetchProjects]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    setCreateError(null);
    try {
      await apiClient<Project>("/projects", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || undefined,
        }),
      });
      setName("");
      setDescription("");
      setShowModal(false);
      await fetchProjects();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setCreateError(err.message);
      } else if (err instanceof Error) {
        setCreateError(err.message);
      } else {
        setCreateError("Failed to create project.");
      }
    } finally {
      setCreating(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex items-center gap-3 text-sm text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin text-teal-400" />
          <span>Verifying authentication session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex-1 max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="w-14 h-14 rounded-2xl bg-teal-500/10 border border-teal-500/30 text-teal-400 mx-auto flex items-center justify-center mb-4">
          <Shield className="w-7 h-7" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Protected Security Workspace</h2>
        <p className="text-sm text-slate-300 max-w-md mx-auto mb-8">
          To manage dependency inventories, view private vulnerability scans, and simulate scenario blast radius, please sign in.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/login"
            className="px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-sm transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/demo"
            className="px-5 py-2.5 rounded-xl bg-navy-800 hover:bg-navy-700 border border-navy-700 text-white font-semibold text-sm transition-colors"
          >
            Try Synthetic Demo
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-8 border-b border-navy-800">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Security Projects</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage your applications, environments, and immutable CycloneDX dependency snapshots
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchProjects()}
            className="p-2.5 rounded-xl bg-navy-800 hover:bg-navy-700 border border-navy-700 text-slate-300 hover:text-white transition-colors"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-400" : ""}`} />
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-sm shadow-md transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="my-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Failed to load projects</div>
            <div className="text-xs text-rose-400/90 mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {/* Project Cards Grid */}
      <div className="mt-8">
        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="h-44 rounded-2xl bg-navy-900/60 border border-navy-800 animate-pulse p-6"
              />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16 bg-navy-900/30 border border-navy-800/80 rounded-2xl p-8">
            <div className="w-12 h-12 rounded-xl bg-navy-800 text-slate-400 mx-auto flex items-center justify-center mb-4">
              <FolderGit2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-white mb-1">No Projects Found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mb-6">
              Create your first project to upload CycloneDX software bill of materials and analyze dependency risks.
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs shadow transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create First Project</span>
            </button>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((p) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}`}
                className="group p-6 rounded-2xl bg-navy-900/80 hover:bg-navy-900 border border-navy-800 hover:border-teal-500/50 shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <h3 className="font-bold text-white text-base group-hover:text-teal-300 transition-colors line-clamp-1">
                      {p.name}
                    </h3>
                    <div className="w-7 h-7 rounded-lg bg-navy-800 flex items-center justify-center text-slate-400 group-hover:text-teal-400 transition-colors shrink-0">
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 line-clamp-2 min-h-[32px]">
                    {p.description || "No project description provided."}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-navy-800/80 flex items-center justify-between text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5" title="Associated Applications / Environments">
                    <Server className="w-3.5 h-3.5 text-teal-400" />
                    <span>{p.asset_count} {p.asset_count === 1 ? "Asset" : "Assets"}</span>
                  </div>

                  <div className="flex items-center gap-1.5" title="Captured Snapshots">
                    <Layers className="w-3.5 h-3.5 text-slate-400" />
                    <span>{p.snapshot_count} {p.snapshot_count === 1 ? "Snapshot" : "Snapshots"}</span>
                  </div>

                  <div className="flex items-center gap-1 text-[10px] text-slate-500">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* New Project Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-navy-900 border border-navy-700 p-6 rounded-2xl shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-1">Create New Project</h2>
            <p className="text-xs text-slate-400 mb-6">
              A project aggregates applications and environments to analyze shared dependency risks.
            </p>

            {createError && (
              <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1" htmlFor="projectName">
                  Project Name *
                </label>
                <input
                  id="projectName"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Payments Monolith"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-navy-950 border border-navy-700 text-white text-sm focus:outline-none focus:border-teal-500 transition-colors"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1" htmlFor="projectDesc">
                  Description
                </label>
                <textarea
                  id="projectDesc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="Primary ecommerce and checkout dependency scope"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-navy-950 border border-navy-700 text-white text-sm focus:outline-none focus:border-teal-500 transition-colors"
                />
              </div>

              <div className="flex justify-end gap-3 mt-6 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  disabled={creating}
                  className="px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-750 text-slate-300 text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !name.trim()}
                  className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-navy-950 text-xs font-bold shadow transition-colors disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
