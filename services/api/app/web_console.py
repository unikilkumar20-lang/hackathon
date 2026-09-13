from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Web Console"])

WEB_CONSOLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RippleGuard — Interactive Security Workspace</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            navy: {
              700: '#1e293b',
              800: '#0f172a',
              900: '#0b132b',
              950: '#060b19',
            },
            teal: {
              300: '#5eead4',
              400: '#2dd4bf',
              500: '#14b8a6',
            }
          },
          fontFamily: {
            sans: ['Inter', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          }
        }
      }
    }
  </script>
  <style>
    body { background-color: #060b19; font-family: 'Inter', sans-serif; }
    .glass { background: rgba(11, 19, 43, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .glass-teal { background: rgba(20, 184, 166, 0.08); border: 1px solid rgba(20, 184, 166, 0.25); }
    .modal-backdrop { background: rgba(6, 11, 25, 0.85); backdrop-filter: blur(8px); }
  </style>
</head>
<body class="text-slate-200 min-h-screen flex flex-col antialiased selection:bg-teal-500 selection:text-navy-950">

  <!-- Header -->
  <header class="border-b border-navy-700/80 bg-navy-900/90 sticky top-0 z-50 backdrop-blur">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-400 font-bold text-lg shadow-inner">
          🛡️
        </div>
        <div>
          <div class="font-bold text-white tracking-tight text-lg flex items-center gap-2">
            <span>RippleGuard</span>
            <span class="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30">Live Workspace</span>
          </div>
          <p class="text-[11px] text-slate-400">Simulate the ripple. Prioritize the repair.</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 border border-navy-700 text-xs font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1.5">
          <span>Swagger API Docs</span>
          <span class="text-slate-500">↗</span>
        </a>

        <!-- Firebase Auth Profile / Sign-in Status -->
        <div id="auth-status-container" class="flex items-center gap-2">
          <button onclick="openAuthModal()" class="px-3.5 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs shadow-md transition-all flex items-center gap-1.5">
            <span>🔑 Sign In / Register</span>
          </button>
        </div>
      </div>
    </div>
  </header>

  <!-- Banner -->
  <div class="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-center text-xs font-semibold text-amber-300 flex items-center justify-center gap-2">
    <span>⚡ Firebase Authentication & PRD Section 17 Multi-App Screening Studio</span>
  </div>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full flex flex-col gap-8">

    <!-- Tab Bar -->
    <div class="flex border-b border-navy-700/80 gap-6 text-sm font-medium">
      <button id="tab-demo-btn" onclick="switchTab('demo')" class="pb-3 border-b-2 border-teal-400 text-teal-300 font-semibold transition-colors flex items-center gap-2">
        <span>🧪 Synthetic Multi-App Demo (PRD Sec 17)</span>
      </button>
      <button id="tab-real-btn" onclick="switchTab('real')" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-2">
        <span>📦 Real CycloneDX SBOM & OSV Ingestion</span>
      </button>
    </div>

    <!-- TAB 1: SYNTHETIC DEMO -->
    <section id="tab-demo" class="flex flex-col gap-8">
      <!-- Top Metrics Row -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="glass p-5 rounded-2xl">
          <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Simulated Source</span>
          <div class="text-lg font-bold font-mono text-white mt-1">tiny-parse@1.0.0</div>
          <span class="text-[11px] text-slate-400">Target shared dependency</span>
        </div>
        <div class="glass p-5 rounded-2xl">
          <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Scoped Applications</span>
          <div class="text-lg font-bold text-white mt-1">5 Assets (Weight 18)</div>
          <span class="text-[11px] text-slate-400">Checkout, Billing, Admin, Docs, Identity</span>
        </div>
        <div class="glass p-5 rounded-2xl">
          <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Lower Exposure Bound</span>
          <div id="demo-lower-stat" class="text-2xl font-black font-mono text-teal-300 mt-1">66.7%</div>
          <span class="text-[11px] text-slate-400">All required gates strictly TRUE</span>
        </div>
        <div class="glass p-5 rounded-2xl">
          <span class="text-xs text-slate-400 uppercase tracking-wider font-semibold">Upper Exposure Bound</span>
          <div id="demo-upper-stat" class="text-2xl font-black font-mono text-amber-300 mt-1">72.2%</div>
          <span class="text-[11px] text-slate-400">Allows UNKNOWN gates (Docs app)</span>
        </div>
      </div>

      <!-- Graph & Interactive Simulation -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Left 2 Cols: Visual Graph Representation -->
        <div class="lg:col-span-2 glass p-6 rounded-2xl flex flex-col gap-6">
          <div class="flex items-center justify-between border-b border-navy-700/60 pb-4">
            <div>
              <h3 class="font-bold text-white text-base">Multi-Application Dependency Graph</h3>
              <p class="text-xs text-slate-400">Shows blast-radius exposure flow from compromised package to assets</p>
            </div>
            <span class="px-2.5 py-1 rounded-md bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-mono">
              Direction: Source → Consumers
            </span>
          </div>

          <!-- Interactive Node Cards Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            
            <!-- Asset 1 -->
            <div class="p-4 rounded-xl bg-navy-800/80 border border-rose-500/30 flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <span class="font-bold text-white text-sm">Checkout Service</span>
                <span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono font-semibold">Weight: 5</span>
              </div>
              <div class="text-slate-400 font-mono text-[11px]">
                tiny-parse → shared-http → <b>Checkout</b> (Gate: TRUE)<br/>
                tiny-parse → auth-helper → <b>Checkout</b> (Gate: TRUE)
              </div>
              <div class="text-[11px] text-rose-400 font-semibold flex items-center gap-1 mt-1">
                <span>⚠️ Reached in Lower & Upper (Parallel Path Synergy)</span>
              </div>
            </div>

            <!-- Asset 2 -->
            <div class="p-4 rounded-xl bg-navy-800/80 border border-rose-500/30 flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <span class="font-bold text-white text-sm">Billing API</span>
                <span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono font-semibold">Weight: 4</span>
              </div>
              <div class="text-slate-400 font-mono text-[11px]">
                tiny-parse → logger-format → <b>Billing</b> (Gate: TRUE)
              </div>
              <div class="text-[11px] text-rose-400 font-semibold flex items-center gap-1 mt-1">
                <span>⚠️ Reached in Lower & Upper</span>
              </div>
            </div>

            <!-- Asset 3 -->
            <div class="p-4 rounded-xl bg-navy-800/80 border border-rose-500/30 flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <span class="font-bold text-white text-sm">Admin Portal</span>
                <span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono font-semibold">Weight: 3</span>
              </div>
              <div class="text-slate-400 font-mono text-[11px]">
                tiny-parse → auth-helper → <b>Admin</b> (Gate: TRUE)
              </div>
              <div class="text-[11px] text-rose-400 font-semibold flex items-center gap-1 mt-1">
                <span>⚠️ Reached in Lower & Upper</span>
              </div>
            </div>

            <!-- Asset 4 -->
            <div class="p-4 rounded-xl bg-navy-800/80 border border-amber-500/30 flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <span class="font-bold text-white text-sm">Developer Docs</span>
                <span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-semibold">Weight: 1</span>
              </div>
              <div class="text-slate-400 font-mono text-[11px]">
                tiny-parse → docs-theme → <b>Docs</b> (Gate: UNKNOWN)
              </div>
              <div class="text-[11px] text-amber-400 font-semibold flex items-center gap-1 mt-1">
                <span>⚡ Reached in Upper only (Uncertain Gate)</span>
              </div>
            </div>

            <!-- Asset 5 -->
            <div class="sm:col-span-2 p-4 rounded-xl bg-navy-800/80 border border-emerald-500/30 flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <span class="font-bold text-white text-sm">Identity Provider</span>
                <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-semibold">Weight: 5</span>
              </div>
              <div class="text-slate-400 font-mono text-[11px]">
                id-vault → <b>Identity</b> (Disconnected from tiny-parse)
              </div>
              <div class="text-[11px] text-emerald-400 font-semibold flex items-center gap-1 mt-1">
                <span>🛡️ Safe · 0 Exposure (No Dependency Path)</span>
              </div>
            </div>

          </div>
        </div>

        <!-- Right Col: Controls & Optimizer -->
        <div class="glass p-6 rounded-2xl flex flex-col gap-6">
          <div class="border-b border-navy-700/60 pb-3">
            <h3 class="font-bold text-white text-base">Counterfactual Optimizer</h3>
            <p class="text-xs text-slate-400">Power-set search for optimal mitigations within budget</p>
          </div>

          <div class="flex flex-col gap-4">
            <div>
              <label class="text-xs font-semibold text-slate-300 flex justify-between mb-1">
                <span>Effort Budget (Units):</span>
                <span id="budget-val" class="text-teal-400 font-mono font-bold text-sm">4</span>
              </label>
              <input id="budget-slider" type="range" min="0" max="6" value="4" oninput="updateBudget(this.value)" class="w-full accent-teal-400 cursor-pointer">
              <div class="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                <span>0 (None)</span>
                <span>2</span>
                <span>4 (Recommended)</span>
                <span>6 (Max)</span>
              </div>
            </div>

            <div>
              <label class="text-xs font-semibold text-slate-300 mb-1 block">Attack Scenario Mode:</label>
              <select id="scenario-mode" onchange="runDemoOptimize()" class="w-full bg-navy-800 border border-navy-700 text-slate-200 text-xs rounded-xl p-2.5 focus:border-teal-400 outline-none">
                <option value="runtime">Runtime Payload Mode</option>
                <option value="install-script-only">Install-Script-Only Mode</option>
              </select>
            </div>

            <button onclick="runDemoOptimize()" class="w-full py-2.5 px-4 rounded-xl bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs shadow-lg shadow-teal-500/20 transition-all">
              ⚡ Compute Optimal Mitigations
            </button>
          </div>

          <!-- Optimizer Results Box -->
          <div id="optimizer-result" class="p-4 rounded-xl bg-navy-950 border border-navy-700 text-xs flex flex-col gap-3">
            <div class="font-bold text-slate-300 uppercase tracking-wider text-[10px]">Optimization Outcome</div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Chosen Controls:</span>
              <span id="opt-chosen-count" class="font-mono font-bold text-teal-300">1 control</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Total Effort Used:</span>
              <span id="opt-cost" class="font-mono font-bold text-white">4 / 4 units</span>
            </div>
            <div class="flex items-center justify-between border-t border-navy-800 pt-2">
              <span class="text-slate-400">Upper Exposure:</span>
              <span id="opt-upper" class="font-mono font-bold text-emerald-400">72.2% → 0.0%</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Absolute Reduction:</span>
              <span id="opt-reduction" class="font-mono font-bold text-emerald-400">72.2 points (100%)</span>
            </div>
            <div id="opt-controls-list" class="text-[11px] text-slate-400 mt-1 border-t border-navy-800 pt-2 flex flex-col gap-1">
              • Replace tiny-parse with verified internal parser (Cost 4)
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- TAB 2: REAL CYCLONEDX INGESTION -->
    <section id="tab-real" class="hidden flex flex-col gap-8">
      <div class="glass p-6 rounded-2xl flex flex-col gap-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-navy-700/60 pb-4">
          <div>
            <h3 class="font-bold text-white text-base">CycloneDX 1.5/1.6 JSON Ingestion & Security Scan</h3>
            <p class="text-xs text-slate-400">Upload a software inventory or test with our valid sample linked to your account</p>
          </div>
          <button onclick="runSampleIngestion()" class="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs shadow transition-colors">
            🚀 Ingest Sample SBOM & Scan
          </button>
        </div>

        <div id="ingest-status" class="hidden p-4 rounded-xl bg-navy-950 border border-teal-500/30 text-xs flex flex-col gap-3 font-mono">
          <div class="text-teal-300 font-bold">Progress Log:</div>
          <div id="ingest-log" class="text-slate-300 leading-relaxed text-[11px]"></div>
        </div>

        <!-- Discovered Findings Table -->
        <div id="findings-container" class="hidden flex flex-col gap-3">
          <div class="font-bold text-white text-sm">Discovered Security Advisories (OSV Real Check):</div>
          <div class="overflow-x-auto rounded-xl border border-navy-700">
            <table class="w-full text-left text-xs text-slate-300">
              <thead class="bg-navy-800 text-slate-400 uppercase font-semibold text-[10px]">
                <tr>
                  <th class="p-3">Package</th>
                  <th class="p-3">Ecosystem</th>
                  <th class="p-3">Advisory ID</th>
                  <th class="p-3">Severity</th>
                  <th class="p-3">Details</th>
                </tr>
              </thead>
              <tbody id="findings-body" class="divide-y divide-navy-800"></tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

  </main>

  <!-- FIREBASE AUTH MODAL -->
  <div id="auth-modal" class="fixed inset-0 z-50 modal-backdrop hidden flex items-center justify-center p-4">
    <div class="w-full max-w-md glass bg-navy-900/95 border border-navy-700/80 p-8 rounded-2xl shadow-2xl relative flex flex-col gap-5">
      
      <!-- Close Button -->
      <button onclick="closeAuthModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg">✕</button>

      <div class="text-center">
        <div class="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 mx-auto flex items-center justify-center text-xl mb-3">
          🔥
        </div>
        <h2 id="modal-title" class="text-xl font-bold text-white">Sign In with Firebase</h2>
        <p class="text-xs text-slate-400 mt-1">Project: <span class="font-mono text-teal-300">ripple-guard</span></p>
      </div>

      <!-- Error Alert -->
      <div id="auth-error" class="hidden p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-xs text-rose-300"></div>

      <!-- Google (Gmail) Sign-In Button -->
      <button onclick="handleGoogleSignIn()" class="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-800 font-semibold text-xs transition-colors flex items-center justify-center gap-3 shadow">
        <svg class="w-4 h-4" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
        </svg>
        <span>Sign in with Google (Gmail)</span>
      </button>

      <div class="flex items-center gap-3 text-slate-600 my-1">
        <div class="flex-1 h-px bg-navy-800"></div>
        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Or with Email</span>
        <div class="flex-1 h-px bg-navy-800"></div>
      </div>

      <!-- Email / Password Form -->
      <form onsubmit="handleEmailSubmit(event)" class="flex flex-col gap-3">
        <div>
          <label class="text-[11px] font-semibold text-slate-300 block mb-1">Email Address</label>
          <input id="auth-email" type="email" required placeholder="you@example.com" class="w-full bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-xl p-2.5 focus:border-teal-400 outline-none">
        </div>

        <div>
          <label class="text-[11px] font-semibold text-slate-300 block mb-1">Password</label>
          <input id="auth-password" type="password" required placeholder="••••••••" class="w-full bg-navy-950 border border-navy-700 text-slate-200 text-xs rounded-xl p-2.5 focus:border-teal-400 outline-none">
        </div>

        <button type="submit" id="submit-auth-btn" class="w-full py-2.5 px-4 rounded-xl bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs transition-colors mt-2">
          Sign In
        </button>
      </form>

      <div class="text-center text-xs text-slate-400 pt-2 border-t border-navy-800">
        <span id="auth-toggle-prompt">Don't have an account?</span>
        <button onclick="toggleAuthMode()" id="auth-toggle-btn" class="text-teal-400 hover:underline font-semibold ml-1">
          Create one now
        </button>
      </div>

    </div>
  </div>

  <footer class="border-t border-navy-800 bg-navy-950/80 py-4 text-center text-xs text-slate-500">
    RippleGuard — Explainable open-source dependency risk and compromise-scenario analysis · Hackathon 2026
  </footer>

  <!-- FIREBASE MODULAR SDK v10 (CDN) -->
  <script type="module">
    import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
    import {
      getAuth,
      GoogleAuthProvider,
      signInWithPopup,
      signInWithEmailAndPassword,
      createUserWithEmailAndPassword,
      signOut,
      onAuthStateChanged
    } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";

    const firebaseConfig = {
      apiKey: "AIzaSyBVGDfN2RLnkTKfM8x2v4SLC_6JUocVMcM",
      authDomain: "ripple-guard.firebaseapp.com",
      projectId: "ripple-guard",
      storageBucket: "ripple-guard.firebasestorage.app",
      messagingSenderId: "81571425592",
      appId: "1:81571425592:web:035980d2f44e12c43aa5cd",
      measurementId: "G-NWD89HY3CN"
    };

    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    window._firebaseAuth = auth;

    let isCreateMode = false;
    window.currentUserToken = null;
    window.currentUser = null;

    // Listen for Auth state
    onAuthStateChanged(auth, async (user) => {
      window.currentUser = user;
      const container = document.getElementById('auth-status-container');
      if (user) {
        try {
          window.currentUserToken = await user.getIdToken();
        } catch (e) {
          console.warn("Could not get ID token:", e);
        }
        const displayName = user.displayName || user.email.split('@')[0];
        container.innerHTML = `
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full bg-teal-500/20 border border-teal-500/40 text-teal-300 font-bold flex items-center justify-center text-xs overflow-hidden">
              ${user.photoURL ? `<img src="${user.photoURL}" class="w-full h-full object-cover">` : displayName[0].toUpperCase()}
            </div>
            <div class="text-left hidden sm:block">
              <div class="text-xs font-semibold text-white leading-tight">${displayName}</div>
              <div class="text-[10px] text-teal-300 font-mono">${user.email}</div>
            </div>
            <button onclick="handleSignOut()" class="px-2.5 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 border border-navy-700 text-xs text-slate-400 hover:text-white transition-colors" title="Sign Out">
              Sign Out
            </button>
          </div>
        `;
      } else {
        window.currentUserToken = null;
        container.innerHTML = `
          <button onclick="openAuthModal()" class="px-3.5 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs shadow-md transition-all flex items-center gap-1.5">
            <span>🔑 Sign In / Register</span>
          </button>
        `;
      }
    });

    window.handleGoogleSignIn = async function() {
      const errBox = document.getElementById('auth-error');
      errBox.classList.add('hidden');
      try {
        const provider = new GoogleAuthProvider();
        provider.setCustomParameters({ prompt: 'select_account' });
        await signInWithPopup(auth, provider);
        closeAuthModal();
      } catch (err) {
        errBox.innerText = err.message;
        errBox.classList.remove('hidden');
      }
    };

    window.handleEmailSubmit = async function(e) {
      e.preventDefault();
      const email = document.getElementById('auth-email').value;
      const pass = document.getElementById('auth-password').value;
      const errBox = document.getElementById('auth-error');
      errBox.classList.add('hidden');

      try {
        if (isCreateMode) {
          await createUserWithEmailAndPassword(auth, email, pass);
        } else {
          await signInWithEmailAndPassword(auth, email, pass);
        }
        closeAuthModal();
      } catch (err) {
        errBox.innerText = err.message;
        errBox.classList.remove('hidden');
      }
    };

    window.handleSignOut = async function() {
      await signOut(auth);
    };

    window.toggleAuthMode = function() {
      isCreateMode = !isCreateMode;
      const title = document.getElementById('modal-title');
      const submitBtn = document.getElementById('submit-auth-btn');
      const prompt = document.getElementById('auth-toggle-prompt');
      const toggleBtn = document.getElementById('auth-toggle-btn');

      if (isCreateMode) {
        title.innerText = "Create Your Account";
        submitBtn.innerText = "Register Account";
        prompt.innerText = "Already have an account?";
        toggleBtn.innerText = "Sign In instead";
      } else {
        title.innerText = "Sign In with Firebase";
        submitBtn.innerText = "Sign In";
        prompt.innerText = "Don't have an account?";
        toggleBtn.innerText = "Create one now";
      }
    };

    window.openAuthModal = function() {
      document.getElementById('auth-error').classList.add('hidden');
      document.getElementById('auth-modal').classList.remove('hidden');
    };

    window.closeAuthModal = function() {
      document.getElementById('auth-modal').classList.add('hidden');
    };
  </script>

  <script>
    function switchTab(tab) {
      if (tab === 'demo') {
        document.getElementById('tab-demo').classList.remove('hidden');
        document.getElementById('tab-real').classList.add('hidden');
        document.getElementById('tab-demo-btn').className = "pb-3 border-b-2 border-teal-400 text-teal-300 font-semibold transition-colors flex items-center gap-2";
        document.getElementById('tab-real-btn').className = "pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-2";
      } else {
        document.getElementById('tab-demo').classList.add('hidden');
        document.getElementById('tab-real').classList.remove('hidden');
        document.getElementById('tab-real-btn').className = "pb-3 border-b-2 border-teal-400 text-teal-300 font-semibold transition-colors flex items-center gap-2";
        document.getElementById('tab-demo-btn').className = "pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-2";
      }
    }

    function updateBudget(val) {
      document.getElementById('budget-val').innerText = val;
    }

    async function runDemoOptimize() {
      const budget = document.getElementById('budget-slider').value;
      const mode = document.getElementById('scenario-mode').value;
      try {
        const res = await fetch(`/demo/optimize?budget=${budget}&mode=${mode}`, { method: 'POST' });
        const data = await res.json();
        
        document.getElementById('opt-chosen-count').innerText = `${data.chosen_controls.length} control(s)`;
        document.getElementById('opt-cost').innerText = `${data.total_cost} / ${budget} units`;
        document.getElementById('opt-upper').innerText = `${data.baseline_upper}% → ${data.optimized_upper}%`;
        
        const rel = data.relative_reduction !== null ? `${data.relative_reduction}%` : 'N/A';
        document.getElementById('opt-reduction').innerText = `${data.absolute_reduction} points (${rel})`;

        const listDiv = document.getElementById('opt-controls-list');
        if (data.chosen_controls.length > 0) {
          listDiv.innerHTML = data.chosen_controls.map(c => `• <b>${c.label}</b> (Effort ${c.cost})`).join('<br/>');
        } else {
          listDiv.innerHTML = '• No controls feasible within this budget.';
        }
      } catch (err) {
        console.error(err);
      }
    }

    async function runSampleIngestion() {
      const statusBox = document.getElementById('ingest-status');
      const logBox = document.getElementById('ingest-log');
      statusBox.classList.remove('hidden');
      
      const authHeader = window.currentUserToken 
        ? `Bearer ${window.currentUserToken}`
        : 'Bearer mock-token-judge:judge@example.com';

      const userDesc = window.currentUser ? `Firebase User (${window.currentUser.email})` : 'Demo Session';
      logBox.innerHTML = `1. Creating Project under ${userDesc}...\\n`;

      try {
        // Step 1: Create project
        const pRes = await fetch('/api/v1/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': authHeader },
          body: JSON.stringify({ name: 'Payment Core Gateway' })
        });
        const project = await pRes.json();
        logBox.innerHTML += `✓ Project created (ID: ${project.id})\\n2. Uploading valid CycloneDX 1.5 SBOM payload...\\n`;

        // Step 2: Upload CycloneDX SBOM
        const sampleSbom = {
          "bomFormat": "CycloneDX",
          "specVersion": "1.5",
          "version": 1,
          "metadata": { "component": { "bom-ref": "gateway@1.0.0", "name": "gateway", "version": "1.0.0", "type": "application" } },
          "components": [
            { "bom-ref": "express@4.19.2", "name": "express", "version": "4.19.2", "purl": "pkg:npm/express@4.19.2" },
            { "bom-ref": "qs@6.11.0", "name": "qs", "version": "6.11.0", "purl": "pkg:npm/qs@6.11.0" },
            { "bom-ref": "debug@4.3.4", "name": "debug", "version": "4.3.4", "purl": "pkg:npm/debug@4.3.4" }
          ],
          "dependencies": [
            { "ref": "gateway@1.0.0", "dependsOn": ["express@4.19.2", "debug@4.3.4"] },
            { "ref": "express@4.19.2", "dependsOn": ["qs@6.11.0"] }
          ]
        };

        const sRes = await fetch(`/api/v1/projects/${project.id}/snapshots`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': authHeader },
          body: JSON.stringify(sampleSbom)
        });
        const snapshot = await sRes.json();
        logBox.innerHTML += `✓ Snapshot parsed & persisted! Nodes: ${snapshot.occurrence_count}, Edges: ${snapshot.edge_count}\\n3. Running OSV security vulnerability check...\\n`;

        // Step 3: Run Enrichment Check
        const eRes = await fetch(`/api/v1/snapshots/${snapshot.id}/enrichment-checks`, {
          method: 'POST',
          headers: { 'Authorization': authHeader }
        });
        const check = await eRes.json();
        logBox.innerHTML += `✓ OSV check complete: status '${check.status}' with ${check.findings_count} findings!\\n4. Fetching Cytoscape dependency graph...\\n`;

        // Step 4: Fetch Graph
        const gRes = await fetch(`/api/v1/snapshots/${snapshot.id}/graph`, {
          headers: { 'Authorization': authHeader }
        });
        const graph = await gRes.json();
        logBox.innerHTML += `✓ Cytoscape graph returned: ${graph.nodes.length} nodes, ${graph.edges.length} edges ready for visual layout!\\n`;

        // Step 5: Fetch Findings
        const fRes = await fetch(`/api/v1/snapshots/${snapshot.id}/findings`, {
          headers: { 'Authorization': authHeader }
        });
        const findings = await fRes.json();
        const findingsContainer = document.getElementById('findings-container');
        const findingsBody = document.getElementById('findings-body');
        
        if (findings.items && findings.items.length > 0) {
          findingsContainer.classList.remove('hidden');
          findingsBody.innerHTML = findings.items.map(item => `
            <tr class="hover:bg-navy-850">
              <td class="p-3 font-mono font-bold text-white">${item.package_name}@${item.package_version}</td>
              <td class="p-3 font-mono uppercase text-teal-400">${item.ecosystem}</td>
              <td class="p-3 font-mono text-amber-300 font-semibold">${item.advisory.external_id}</td>
              <td class="p-3 font-mono text-slate-400">${item.match_details.severity || 'Medium'}</td>
              <td class="p-3 text-slate-300 text-[11px]">${item.match_details.summary || 'Security advisory match'}</td>
            </tr>
          `).join('');
        }
      } catch (err) {
        logBox.innerHTML += `\\n❌ Error: ${err.message}`;
      }
    }

    // Run initial optimize on load
    runDemoOptimize();
  </script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
def get_web_console():
    """Interactive visual Web Console for RippleGuard."""
    return HTMLResponse(content=WEB_CONSOLE_HTML, status_code=200)
