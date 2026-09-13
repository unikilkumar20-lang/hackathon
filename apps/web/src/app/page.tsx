import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  FileCode,
  Network,
  Sliders,
  Database,
  Lock,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex-1 flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-20 border-b border-navy-800">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-teal-900/20 via-navy-950 to-navy-950 -z-10" />
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-medium mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Simulate the ripple. Prioritize the repair.</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6">
            Explainable Open-Source <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-teal-300 to-cyan-400">
              Dependency Risk Simulation
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg text-slate-300 mb-10 leading-relaxed">
            Stop guessing the blast radius of a compromised package. Model downstream exposure across your applications, test runtime vs. install-script scenarios, and optimize mitigations within your engineering effort budget.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/demo"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-sm shadow-lg shadow-teal-500/20 transition-all flex items-center justify-center gap-2 group"
            >
              <span>Try Synthetic Demo</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>

            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-navy-800 hover:bg-navy-700 border border-navy-700 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              <Lock className="w-4 h-4 text-slate-400" />
              <span>Analyze My Project</span>
            </Link>
          </div>

          <div className="mt-8 text-xs text-slate-400">
            No signup required for the interactive synthetic demo · Publicly inspectable graph logic
          </div>
        </div>
      </section>

      {/* Core Principles & Honest Boundaries */}
      <section className="py-16 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-white mb-3">Honest Security Modeling</h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            RippleGuard is mathematically rigorous and explainable. We never guess internal code without manifests, execute malware, or fabricate compromise claims.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-navy-900/60 border border-navy-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center mb-4">
                <Network className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base mb-2">Occurrence & Cycle Safe Traversal</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Graph evaluation preserves duplicate resolved versions, distinct occurrence paths, and cyclic dependencies without collapsing context or dropping edges.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-navy-800 text-xs text-teal-400 font-mono">
              Powered by NetworkX
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-navy-900/60 border border-navy-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center mb-4">
                <Sliders className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base mb-2">Tri-State Gates & Payload Modes</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Explicitly evaluate true, false, and unknown execution gates. Disabling install scripts blocks build-time hooks, but will never falsely claim to eliminate runtime exposure.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-navy-800 text-xs text-teal-400 font-mono">
              Lower & Upper Exposure Bounds
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-navy-900/60 border border-navy-800 flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center mb-4">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base mb-2">Real OSV Security Evidence</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Advisories come directly from live OSV records with explicit provider timestamps. Unknown or unverified packages report unconfirmed status, never false &quot;safety&quot;.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-navy-800 text-xs text-teal-400 font-mono">
              Immutable Findings & Time-stamped
            </div>
          </div>
        </div>
      </section>

      {/* Supported Inputs Section */}
      <section className="py-12 bg-navy-900/40 border-t border-navy-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-lg font-bold text-white mb-6 text-center">Supported Inventory Formats</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-navy-900/80 border border-teal-500/30 flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-white text-sm">CycloneDX JSON (1.5 & 1.6)</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Full component dependency graph, purls, hashes, and metadata root components. Validated and immutable.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-navy-900/50 border border-navy-800 flex items-start gap-3 opacity-60">
              <FileCode className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-white text-sm">npm package-lock v3 & GitHub</h4>
                  <span className="text-[10px] px-1.5 py-0.5 bg-navy-800 text-amber-300 rounded font-medium">Planned P1</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Nested package-lock resolution and direct GitHub commit-pinned manifest imports.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
