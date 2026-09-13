"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, ShieldAlert, ArrowLeft, Layers, Server, Activity, FileCheck } from "lucide-react";

export default function DemoPage() {
  return (
    <div className="flex-1 flex flex-col w-full">
      {/* Prominent Mandatory Synthetic Banner */}
      <div className="bg-amber-500/15 border-b border-amber-500/30 px-4 py-3 text-center text-xs font-semibold text-amber-300 flex items-center justify-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
        <span>Synthetic scenario — not a real scan. All packages, weights, and advisories in this sandbox are synthetic fixtures.</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1 flex flex-col">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link
                href="/"
                className="text-slate-400 hover:text-white text-xs flex items-center gap-1 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Home</span>
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-xs text-teal-400 font-medium">Public Demo Sandbox</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
              <span>Synthetic Multi-Application Fixture</span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300">
                5 Assets · Weight 18
              </span>
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="px-4 py-2 rounded-xl bg-navy-800 hover:bg-navy-700 border border-navy-700 text-white text-xs font-semibold transition-colors"
            >
              Analyze My Project
            </Link>
          </div>
        </div>

        {/* Demo Overview Card */}
        <div className="grid lg:grid-cols-4 gap-6 mb-8">
          <div className="p-5 rounded-2xl bg-navy-900/70 border border-navy-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>Source Package</span>
              <Layers className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-lg font-bold text-white font-mono">tiny-parse@1.0.0</div>
            <div className="text-[11px] text-slate-400 mt-1">Simulated compromised dependency</div>
          </div>

          <div className="p-5 rounded-2xl bg-navy-900/70 border border-navy-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>Scoped Assets</span>
              <Server className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-lg font-bold text-white">5 Applications</div>
            <div className="text-[11px] text-slate-400 mt-1">Checkout(5), Billing(4), Admin(3), Docs(1), Identity(5)</div>
          </div>

          <div className="p-5 rounded-2xl bg-navy-900/70 border border-navy-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>Baseline Exposure</span>
              <Activity className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-lg font-bold text-amber-300 font-mono">66.7% – 72.2%</div>
            <div className="text-[11px] text-slate-400 mt-1">Lower: 12/18 · Upper: 13/18 reached</div>
          </div>

          <div className="p-5 rounded-2xl bg-navy-900/70 border border-navy-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>Fixture Provenance</span>
              <FileCheck className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-lg font-bold text-teal-300 font-mono">PRD Section 17</div>
            <div className="text-[11px] text-slate-400 mt-1">Deterministic, zero external calls</div>
          </div>
        </div>

        {/* Placeholder Workspace Area for Milestones 3-6 */}
        <div className="flex-1 min-h-[420px] rounded-2xl bg-navy-900/40 border border-navy-800 p-8 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 rounded-xl bg-navy-800 text-teal-400 flex items-center justify-center mb-4">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white mb-2">Synthetic Graph & Scenario Lab</h3>
          <p className="text-xs text-slate-400 max-w-lg mb-6 leading-relaxed">
            The full interactive Cytoscape.js ELK graph canvas, runtime/install-script gate toggles, and counterfactual mitigation optimizer will be mounted here across Milestones 3 through 6.
          </p>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-800/80 border border-navy-700 text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
            <span>Milestone 1 Foundation Verified · Public Demo Shell Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}
