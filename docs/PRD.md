# RippleGuard — Product Requirements Document

**Build target:** Antigravity IDE · **Version:** 1.0 · **Product:** Explainable open-source dependency risk and compromise-scenario analysis

> **Tagline:** Simulate the ripple. Prioritize the repair.
>
> **Mandatory architecture decision:** Firebase is used **only for authentication**. PostgreSQL stores all application data. Do not use Firestore, Realtime Database, Firebase Storage, Firebase Hosting, or Firebase Functions.

## 1. Product goal

Build a functional web application that accepts a software dependency inventory, identifies known security advisories, visualizes dependency relationships, and simulates the potential downstream exposure if a selected package were compromised. Help a developer choose preventative mitigations within an engineering-effort budget, with understandable evidence and assumptions.

This is not a tool that can discover an arbitrary application's internal dependencies from its name or public website. It is not an antivirus, malware sandbox, or proof of exploitability.

### The winning product moment

A developer selects a small shared dependency and sees which important applications could be exposed. They change the attack scenario, compare fixes, and see the recommendation change. Disabling install scripts helps an install-script-only scenario, but does not stop malicious runtime code. Every result exposes its dependency path, assumptions, and remaining uncertainty.

### Primary users

- Developer: understand the packages in an application and decide what to investigate.
- Security reviewer: trace shared dependencies across applications and prioritize remediation.
- Hackathon judge: understand the problem and verify the differentiator within 90 seconds.

### Success criteria

1. A judge can complete the synthetic demo without external API availability.
2. An authenticated user can upload a supported real file, obtain a persisted graph, and request a real OSV lookup.
3. No result conflates a vulnerability, reported malicious package, and hypothetical compromise.
4. Every exposure result has inspectable paths and assumptions.
5. The mitigation engine recomputes exposure, including parallel paths; it does not merely subtract arbitrary scores.

## 2. Scope and implementation priority

Build one working vertical slice at a time. Do not build all integrations at once.

| Priority | Deliverables |
|---|---|
| P0 — Core screening build | Firebase sign-in; project CRUD; PostgreSQL persistence; CycloneDX JSON import; graph; synthetic multi-app fixture; real OSV enrichment; runtime/install scenario engine; evidence drawer; counterfactual optimizer; JSON report; tests |
| P1 — After P0 passes | npm package-lock v3 import; public GitHub dependency-file import; critical-dependency leaderboard; in-app scan-change notifications; background job worker; deps.dev metadata |
| P2 — Optional | Scheduled rescans; email alerts through a separate provider; private GitHub OAuth integration; optional cited AI explanations; PDF reports; large-graph optimization |

**Not in this release:** automatic code fixes, automatic pull requests, executing package code, installing uploaded dependencies, arbitrary website scanning, malware execution, exhaustive exploitability analysis, enterprise organizations/RBAC, npm lockfile v1/v2, support for every ecosystem.

No feature may appear enabled if it is a nonfunctional placeholder. Deferred items should be absent or explicitly labeled “Planned.”

## 3. Stack and boundaries

| Layer | Choice | Responsibility |
|---|---|---|
| Web | Next.js App Router, React, TypeScript | Screens, navigation, client interactions |
| Styling | Tailwind CSS, shadcn/ui, Lucide | Accessible visual system and icons |
| Forms / API state | React Hook Form, Zod, TanStack Query | Form validation, typed API calls, request state |
| Graph | Cytoscape.js, cytoscape-elk / ELK | Layout, selection, filters, route highlighting |
| API | Python, FastAPI, Pydantic | Validation, authorization, orchestration, OpenAPI |
| Analysis | NetworkX | Directed graph traversal, path witnesses, criticality |
| Persistence | PostgreSQL, SQLAlchemy, Alembic | Projects, immutable snapshots, evidence, runs, alerts |
| Authentication only | Firebase Authentication client SDK + Firebase Admin SDK | Google and email/password sign-in; backend ID-token verification |
| Enrichment | OSV API; deps.dev in P1 | Known advisories and supplemental package metadata |
| Testing | pytest, Hypothesis, Vitest, Playwright | Algorithm, API, UI and end-to-end checks |
| Local infrastructure | Docker Compose for API + PostgreSQL | Repeatable local setup |
| UI/UX planning | Figma, FigJam | Optional screen planning; not runtime dependencies |
| Optional AI | sentence-transformers MiniLM + Ollama Qwen | Evidence retrieval and cited explanation, never risk computation |

Use compatible stable dependency versions available at build time. Pin them in lockfiles. Document chosen versions; do not install packages simply because their names appear in a generated plan.

**Keep the backend a modular monolith.** Ingestion, enrichment, analysis and optimization are Python modules within the same service, not separate microservices. PostgreSQL plus NetworkX is sufficient; do not add Neo4j, Redis, Kubernetes or a vector database for P0.

## 4. Authentication and access control

### Firebase setup

Enable Google sign-in and email/password in Firebase Authentication. Configure authorized domains for localhost and the deployed frontend. Support registration, login, logout, password reset, and email verification UX. If email verification is required by configuration, enforce it on the API as well as the frontend.

### Request flow

1. User signs in using the Firebase browser SDK.
2. Frontend obtains an ID token through the SDK and attaches `Authorization: Bearer <token>` to API calls.
3. FastAPI verifies signature, expiry, issuer and audience using Firebase Admin; use the configured Firebase project, never a client-supplied project identifier.
4. API identifies the user by verified Firebase UID and upserts the local user record.
5. Every project, snapshot, evidence, scenario, report and notification lookup checks ownership through that user.

Do not trust a UID, owner ID, email or role sent in a request body. Return 401 for invalid authentication and 404 for inaccessible resource IDs without revealing another user's data. On token expiry, refresh through the Firebase SDK and retry once; avoid infinite retry loops. Do not manually store ID tokens in localStorage. Keep Firebase service credentials exclusively on the server; never prefix them `NEXT_PUBLIC_`.

Frontend route protection is UX, not authorization. Do not add NextAuth, custom password storage, or a second authentication system.

### Demo access

`/demo` is public and uses a bundled synthetic fixture. It requires no Firebase or OSV call and has a prominent **“Synthetic scenario — not a real scan”** banner. It cannot read or modify private projects. Protected APIs must fail closed if Firebase configuration is missing. A locally configured Firebase Auth Emulator may be used for tests only; never enable emulator or authentication bypass settings in production.

## 5. Core user journeys

### A. New user → first real scan

Sign up → create a project → add an application/environment and weight → upload CycloneDX JSON → inspect validation/coverage summary → save immutable snapshot → run OSV checks → inspect findings and dependency paths.

### B. Scenario analysis

Open a snapshot → choose a source package → choose runtime or install-script-only scenario → review assumptions and unknowns → calculate exposure → select an affected application → inspect its witness path and evidence.

### C. Mitigation comparison

Open a run → define candidate preventative controls and effort → set budget → optimize → compare before/after exposure → inspect remaining routes → export the report. All changes affect a scenario copy, never the original snapshot or real repository.

### D. Multi-application analysis

A project is a collection of application/environment assets. A snapshot can contain several uploaded inventories, each attached to an asset. If the same package-version appears in multiple applications, aggregate its identity for the interface but preserve application-specific resolved graph occurrences. A scenario can target all occurrences of that version in the snapshot or a selected occurrence; label the selected scope.

### E. Monitoring (P1/P2)

Manually rescan the latest saved inventory and compare advisory results with the prior successful check. Display new/changed findings in an in-app notification center. P2 adds scheduling and optional email. Clearly state that rescanning an old inventory does not detect a deployment's dependency changes: the user must upload or synchronize a current inventory.

## 6. Screens and UI/UX requirements

### Design direction

Professional security workspace, not a terminal imitation. Dark navy background, teal primary actions, amber uncertainty, red known-security warnings. Use readable text, clear spacing and restrained animation. Do not communicate status through color alone.

### Routes

| Route | Required content |
|---|---|
| `/` | Concise pitch; “Try synthetic demo”; “Analyze my project”; honest supported-input list |
| `/login`, `/signup`, `/reset-password` | Firebase flows, loading/error states |
| `/demo` | Self-contained synthetic scenario lab with reset and disclaimer |
| `/dashboard` | Project cards; inventory counts; most recent scan status; create project |
| `/projects/[id]` | Application assets, weights, import history, inventory freshness |
| `/projects/[id]/import` | File upload, format constraints, validation warnings, asset mapping |
| `/projects/[id]/snapshots/[snapshotId]` | Dependency explorer and findings tabs |
| `/projects/[id]/runs/[runId]` | Scenario, impact, mitigations, evidence and export |
| `/settings` | Account information and authentication actions |

### Analysis workspace

- Top bar: project, snapshot timestamp, real/synthetic badge, evidence freshness, export.
- Left panel: search, source package, scenario, asset scope, gates, budget.
- Center: dependency graph with zoom, fit, legend, keyboard-accessible alternative table.
- Right panel: exposure range, affected assets, evidence, selected-node details.
- Lower panel/tabs: Findings, Paths, Mitigation comparison, Assumptions.

**Metric labels:** “Known advisories,” “Potentially exposed applications,” “Weighted exposure range,” and “Last successful security check.” Never label a hypothetical score “Chance of being hacked.”

Graph default direction is **consumer → dependency**. A “Downstream impact” toggle reverses the rendered direction and labels it **dependency → consumer**. Do not silently change semantics.

For each screen handle loading, empty, success, validation error, unauthorized, and network failure. A failed external lookup is not a zero-findings success. Support keyboard focus, visible labels, sufficient contrast, reduced motion and responsive layouts. On small screens prioritize tables and detail panels over a full graph canvas.

## 7. Input ingestion and graph correctness

### P0: CycloneDX JSON

Support a documented subset of CycloneDX 1.5 and 1.6 JSON: components, metadata/root component, dependency references, purls, names, versions and hashes when present. Validate against the applicable schema and explicitly describe fields not used. Do not claim complete support for every CycloneDX feature.

Require a distinct `bom-ref` for referenced components and validate dangling dependency references. Handle an application root in `metadata.component`. If dependencies or roots are missing, mark topology incomplete and ask the user to map a root; do not silently invent a complete graph. A component list may still support package advisory checks without supporting reliable path analysis.

Use a maintained package-URL parser. Preserve ecosystem, namespace, name, version, qualifiers and subpath as relevant. If the package cannot be identified for a provider, retain it and label enrichment unsupported or unresolved.

### P1: npm package-lock v3

Resolve dependencies from the lockfile's package locations and nearest applicable installed dependency path. Preserve duplicate versions, nesting, optional/dev flags, aliases and workspace/link behavior. Do not resolve every dependency by package name alone. For unsupported links/workspaces, preserve an unresolved reference and report the limitation rather than infer an edge. Never run `npm install` or lifecycle scripts on uploaded inputs.

### P1: GitHub import

Accept public GitHub repository URLs only. Read supported dependency files through a server-side GitHub API adapter; do not accept arbitrary download URLs, clone and execute projects, or request users' GitHub passwords. Restrict hosts, URL formats, redirects, response sizes and timeouts. Show discovered files for selection; ask for a branch when needed. Record the commit SHA and file path for reproducibility. Private repositories require a later least-privilege integration; Firebase login does not grant repository access.

### Limits and identity

Initial limits: 10 MB per upload, 10,000 occurrence nodes and 50,000 edges per snapshot. Enforce limits before expensive analysis and return actionable errors. Parse JSON only for P0; archives are unsupported.

Maintain two identities:

- **Package identity:** canonical ecosystem/name/version/purl information for advisory matching and cross-app aggregation.
- **Occurrence identity:** snapshot + inventory/application + resolved path or `bom-ref`; actual graph traversal uses occurrences.

Do not collapse graph occurrences solely because they share package name and version: their dependency resolution or context may differ. A project-wide package compromise scenario seeds matching occurrences explicitly.

Store immutable imports and snapshots, SHA-256 hashes, parser versions, warnings and evidence references. One snapshot can include multiple inventories. User weights and later scenario overrides must not mutate historical runs.

## 8. Security enrichment and finding language

### OSV in P0

Use a backend adapter to query supported package identities with their resolved versions. Consult official provider documentation when implementing requests, pagination, batch limits and advisory details. Deduplicate requests by identity, cache results with a configurable TTL, rate-limit per user, and use bounded retries/backoff. Store provider status and timestamps separately from results.

Persist advisory IDs, aliases, affected-version details, summary, source URLs, available severity, modified time and retrieval time. Keep aliases associated to avoid double-counting the same advisory; do not merge unrelated advisories by title. Preserve source severity without inventing CVSS values. A reported fixed version is not proof that upgrading is compatible or that every issue is resolved.

### Status vocabulary

Use separate dimensions rather than one misleading safety badge:

- **Check status:** pending / complete / partial / failed / unsupported.
- **Known vulnerability evidence:** advisory matches / no known matches found.
- **Malicious-package evidence:** reported malicious by an identified source / no such evidence available.
- **Scenario status:** hypothetical source selected / not selected.

“No known matches” always includes provider, time and coverage. Never say “safe” merely because OSV returned no records. Only show reported compromise/maliciousness when an explicit source supports that claim for the relevant package/version. Do not infer it from CVSS or dependency centrality.

### deps.dev in P1

Supplement package metadata and links when supported. Label registry-resolved dependency information as supplemental: it must not silently replace the uploaded application's resolved graph.

## 9. Analysis model — implementation specification

### What the model is

An explainable graph model plus a counterfactual optimization algorithm. No model training, invented training dataset or prediction-accuracy claim is required. NetworkX performs the core computation; an LLM is not required to make the app intelligent.

### Graph and scenario

Use a directed graph with occurrence nodes and application/environment asset nodes. Store consumer → dependency edges. Reverse traversal from scenario sources finds downstream consumers. Represent multiple context-specific edges when necessary.

Edge/context predicates have three states: `true`, `false`, `unknown`. Record whether each is a fixture value, parser-derived fact, user assumption or external evidence. Mere installation or manifest presence does not establish runtime execution. Unsupported runtime/build context defaults to unknown, not true.

A scenario contains source occurrence IDs or package identity scope, payload mode, asset scope, gate overrides, asset weights and assumptions. Reject missing sources, out-of-snapshot IDs, empty asset scope and invalid weights. Weights are integers 1–5 with default 3 and a clear explanation that they are user-assigned business importance.

### Exposure calculation

- Lower set: traverse only eligible paths whose required gates are all true.
- Upper set: allow true and unknown gates; false gates block the path.
- Apply source and terminal asset/environment gates as well as edge gates.
- Count each application/environment asset once even if multiple paths reach it.

For scoped assets `A` with weights `w(a)`:

```
lower_index = 100 * sum(w(a) for a in lower_reached_assets) / sum(w(a) for a in A)
upper_index = 100 * sum(w(a) for a in upper_reached_assets) / sum(w(a) for a in A)
```

These are **conditional weighted-exposure indices**. The range describes the stated unknown gates, not statistical confidence, infection likelihood, or the full effect of omitted dependencies. The lower number does not prove exploitation. Incomplete topology receives a separate warning; bounds cannot account for edges that were never supplied.

### Payload modes

**Runtime:** evaluate runtime relevance and execution assumptions. `ignore-scripts` has no effect.

**Install-script-only:** evaluate whether the selected source is installed in the asset's build environment and whether lifecycle scripts are allowed there. Apply the scripts policy at the terminal build/environment gate, not independently to every dependency edge. Known excluded dev dependencies are blocked for that environment; unclear installation context is unknown. Scripts disabled blocks only the selected install-script mechanism, not all package installation attacks.

Controls are preventative and assumed applied before malicious execution. If compromise already occurred, show an incident-response caveat: revoking credentials and rebuilding/verifying in a clean environment may be necessary.

### Paths and certificates

Use cycle-safe traversal. Return a deterministic witness path for each lower- and upper-reached asset, listing occurrence IDs, edge IDs, gate states and provenance. If more paths exist, state that the displayed witness is not exhaustive. Limit optional alternate-path enumeration and label truncation. The optimizer must use full reachability, not only the displayed path.

### Critical dependency ranking (P1)

Run the same selected scenario for candidate package identities. Rank by upper weighted exposure; display lower exposure, distinct affected-asset count, uncertainty gap and advisory evidence separately. Call the rank “Hypothetical impact,” not confirmed compromise risk. Paginate and cache results; cap interactive leaderboard work and use jobs for large snapshots.

## 10. Counterfactual mitigation optimizer

### Candidate control types

- Disable lifecycle scripts for selected build environments — install-script-only effect.
- Exclude a selected dependency route from an asset's modeled deployment — hypothetical graph edit, may break functionality.
- Replace/remove a selected occurrence or dependency subtree — user-confirmed simulated edit, with compatibility caveat.
- Remove the selected version from all scoped environments via a verified replacement inventory — supported only when that replacement graph is supplied; otherwise mark as assumed replacement.

Do not pretend to know a compatible safe upgrade for every package. Do not claim a network-isolation control prevents all malicious runtime behavior. Each control defines exact edited nodes/edges/gates, mechanism scope, positive integer effort units and operational trade-offs. Effort units are estimates, not measured hours.

### Selection rule

For P0 allow at most eight enabled candidate controls. Enumerate feasible subsets, include the empty set, apply edits to a copy, rerun lower/upper evaluation, and choose the smallest upper exposure. Tie-break by lower total effort and then sorted stable control IDs. Validate mutually exclusive controls and reject references outside the snapshot.

Do not sum individual benefits: parallel routes can create combined effects. For more than eight controls ask the user to narrow candidates in P0. A later heuristic must be explicitly labeled approximate.

### Display

Before/after lower and upper values; selected controls; total effort/budget; absolute percentage-point reduction; relative upper reduction where baseline upper is nonzero; residual assets/paths; assumptions and side effects. If baseline is zero, relative reduction is `null`/“Not applicable,” not division by zero. A zero result means “No modeled exposure under this scenario,” never “Completely safe.”

## 11. Data model

Use UUIDs, UTC timestamps, foreign keys and explicit ownership. PostgreSQL JSONB is allowed for immutable source payloads and versioned scenario/report documents; relational tables represent queryable entities.

| Table | Essential fields |
|---|---|
| users | id, firebase_uid unique, email nullable, display_name nullable, created_at |
| projects | id, owner_user_id, name, description, created_at |
| assets | id, project_id, name, environment, default_weight |
| snapshots | id, project_id, content_hash, parser_version, topology_status, created_at |
| inventories | id, snapshot_id, asset_id, source_type, source_ref, source_hash, sanitized source JSON, warnings |
| package_identities | id, ecosystem, namespace, name, version, canonical_purl |
| occurrences | id, snapshot_id, inventory_id, package_identity_id nullable, local_ref, metadata |
| edges | id, snapshot_id, from_occurrence/root, to_occurrence, context, gate_default, provenance |
| snapshot_assets | snapshot_id, asset_id, root_ref, captured_weight, environment_context |
| enrichment_checks | id, snapshot_id, provider, status, coverage, started_at, finished_at, error |
| advisories | id, provider, external_id, aliases, source_url, details, retrieved_at |
| findings | id, check_id, package_identity_id, advisory_id, match_details |
| evidence | id, snapshot_id, kind, source_ref, timestamp, content_hash, trust_label, details |
| runs | id, snapshot_id, scenario_json, result_json, graph/model_version, created_at |
| controls | id, run_id, label, cost, edit_json, mechanism_scope, assumptions |
| optimization_runs | id, run_id, budget, candidate_set_hash, chosen_controls, result_json, optimizer_version |
| notifications (P1) | id, user_id, project_id, dedupe_key unique, finding_ref, read_at, created_at |
| jobs (P1) | id, project_id, type, status, progress, lease/retry fields, error, created_at |

Resolve exact edge/root representation during schema design; use constraints that prevent cross-snapshot references. Include advisory mappings for unsupported/unresolved packages without silently dropping nodes. A new enrichment check does not rewrite historical evidence in saved reports.

## 12. API contract

Prefix `/api/v1`. Authentication required except health and explicitly public fixture resources. Use UUID strings and ISO 8601 UTC times. Generate frontend API types from OpenAPI rather than maintaining inconsistent handwritten DTOs.

| Method / path | Purpose |
|---|---|
| GET `/health` | Liveness; no secrets |
| GET `/ready` | Readiness; sanitized status |
| GET `/me` | Verified current user |
| GET/POST `/projects` | Paginated list / create |
| GET/PATCH/DELETE `/projects/{project_id}` | Owned project management; deletion requires confirmation in UI |
| GET/POST `/projects/{project_id}/assets` | Asset setup |
| POST `/projects/{project_id}/snapshots` | Multipart inventory import and asset mapping; atomic validated snapshot creation |
| GET `/projects/{project_id}/snapshots` | Paginated inventory history |
| GET `/snapshots/{snapshot_id}` | Metadata, warnings, graph summary |
| GET `/snapshots/{snapshot_id}/graph` | Graph or bounded neighborhood; include truncation information |
| POST `/snapshots/{snapshot_id}/enrichment-checks` | Run OSV enrichment; persist complete/partial/failed outcome |
| GET `/snapshots/{snapshot_id}/findings` | Paginated findings and check coverage |
| POST `/runs` | Evaluate and save immutable scenario |
| GET `/runs/{run_id}` | Saved scenario, bounds and paths |
| POST `/runs/{run_id}/optimizations` | Evaluate supplied controls and budget; persist comparison |
| GET `/runs/{run_id}/evidence` | Evidence used by this run |
| GET `/runs/{run_id}/export` | Versioned JSON attachment |
| GET `/snapshots/{snapshot_id}/criticality` | P1 hypothetical-impact leaderboard |
| GET/PATCH `/notifications` | P1 own notifications / mark specified IDs read |
| GET `/jobs/{job_id}` | P1 job progress |

P0 can use synchronous bounded processing with strict timeouts and an explicit size cap for real enrichment. Do not launch untracked background work and return a fake completed scan. P1 adds a durable PostgreSQL-backed job worker, leases, retries and polling; interrupted jobs become retryable or failed, not permanently “running.”

Example scenario request (IDs are illustrative placeholders):

```json
{
  "snapshot_id": "<uuid>",
  "source": {"kind": "package_identity", "id": "<uuid>", "scope": "all_matching_occurrences"},
  "mode": "runtime",
  "asset_ids": ["<uuid>"],
  "asset_weights": {"<asset_uuid>": 5},
  "gate_overrides": [
    {"target_type": "edge", "target_id": "<uuid>", "value": "unknown", "reason": "Execution not verified"}
  ]
}
```

Run response includes `run_id`, `snapshot_id`, `model_version`, `lower_index`, `upper_index`, reached asset IDs, total scoped weight, path certificates, evidence IDs, topology warnings, assumptions and evaluated timestamp. Compute and store full precision; round for display only.

Standard error envelope:

```json
{"error":{"code":"UNSUPPORTED_INPUT","message":"Upload CycloneDX 1.5 or 1.6 JSON.","details":[],"request_id":"<id>"}}
```

Use appropriate 400/401/404/409/413/422/429/503 statuses. Apply pagination consistently. Limit concurrent enrichments per user and deduplicate repeated identical requests. Exports include input hashes, coverage, scan timestamps, algorithm versions and caveats, but never tokens or service credentials.

## 13. Optional AI model usage

Do not implement until deterministic analysis and tests pass. No AI provider is required to run the core app.

Optional pipeline:

1. Retrieve only this authorized run's evidence and computed results.
2. Use `all-MiniLM-L6-v2` locally to retrieve relevant passages, only if the evidence corpus justifies retrieval. For small reports use direct evidence selection instead.
3. Use a configurable local Ollama Qwen model, such as Qwen2.5-7B-Instruct when hardware permits, to produce a short explanation.
4. Require evidence IDs for claims and preserve all computed numbers.
5. Validate IDs and structured output; reject unsupported numerical assertions. Fall back to a deterministic template on timeout or validation failure.

Do not use the LLM to discover vulnerabilities, set gate truth, choose mitigations, calculate exposure or declare compromise. Never send private inventories to a third-party model without explicit user consent. Treat advisory prose and repository text as untrusted input, not instructions.

## 14. Repository structure

```text
rippleguard/
├── apps/
│   └── web/
│       ├── src/app/                 # Routes and layouts
│       ├── src/components/
│       │   ├── ui/
│       │   ├── graph/
│       │   ├── scenarios/
│       │   └── evidence/
│       ├── src/features/            # Auth, projects, imports, findings, runs
│       ├── src/lib/
│       │   ├── firebase-client.ts
│       │   ├── api-client.ts
│       │   └── generated/          # OpenAPI-generated types
│       ├── src/demo/               # Public, explicitly synthetic fixture
│       ├── tests/
│       ├── package.json
│       └── .env.example
├── services/
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── core/              # Config, Firebase verification, errors
│       │   ├── api/v1/            # Route modules
│       │   ├── db/                # Session and SQLAlchemy models
│       │   ├── schemas/           # Pydantic request/response contracts
│       │   ├── ingestion/         # CycloneDX, P1 npm/GitHub adapters
│       │   ├── enrichment/        # OSV client, caching, provenance
│       │   ├── analysis/          # Gates, traversal, certificates
│       │   ├── optimization/      # Control edits and subset evaluation
│       │   ├── reporting/         # Stable JSON export
│       │   └── jobs/              # P1 durable worker
│       ├── migrations/            # Alembic
│       ├── tests/unit/
│       ├── tests/integration/
│       ├── pyproject.toml
│       └── .env.example
├── fixtures/
│   ├── synthetic-demo/
│   ├── cyclonedx/
│   └── invalid-inputs/
├── tests/e2e/
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── MODEL.md
│   ├── SECURITY.md
│   ├── DEMO.md
│   └── IMPLEMENTATION_STATUS.md
├── infra/docker-compose.yml
├── .github/workflows/ci.yml
├── .gitignore
└── README.md
```

## 15. Environment configuration and deployment

Frontend `.env.example`:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=replace_me
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=replace_me
NEXT_PUBLIC_FIREBASE_PROJECT_ID=replace_me
NEXT_PUBLIC_FIREBASE_APP_ID=replace_me
```

Backend `.env.example`:

```dotenv
APP_ENV=development
DATABASE_URL=postgresql+psycopg://rippleguard:local_password@localhost:5432/rippleguard
FIREBASE_PROJECT_ID=replace_me
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/outside/repo/service-account.json
CORS_ORIGINS=http://localhost:3000
MAX_UPLOAD_BYTES=10485760
MAX_GRAPH_NODES=10000
MAX_GRAPH_EDGES=50000
OSV_CACHE_TTL_SECONDS=21600
ENABLE_OPTIONAL_AI=false
```

Inside Docker use the database service hostname, not localhost. Public Firebase web configuration is distinct from the secret Admin credential; do not confuse their treatment. Use secret mounts or managed credentials in deployment, never bake credentials into images. Commit examples only.

Run frontend locally and API/PostgreSQL via Compose, with documented migrations and seed commands. Optional deployment: Next.js on Vercel, FastAPI on a container-capable host, and managed PostgreSQL. Choose providers only after checking current limits. Firebase remains authentication-only. Configure HTTPS, precise CORS origins and Firebase authorized domains. No hardcoded deployment URL or public video link.

## 16. Security and reliability requirements

- Never execute uploaded code or install dependencies from submitted projects.
- Enforce ownership on nested endpoints, exports and background jobs.
- Sanitize displayed advisory text; no raw HTML rendering or untrusted executable Markdown.
- Bound file size, nesting, node/edge count, layout work, external requests and optimization work.
- Do not log tokens, credentials or complete private inventories.
- Fixed provider hosts for OSV/deps.dev clients; SSRF defenses for repository import.
- Distinguish stale/partial/failed evidence from successful no-findings results.
- Use database transactions for imports; invalid imports leave no partial snapshot.
- Preserve reproducibility using immutable snapshots and versioned result artifacts.
- Make UI cancellation honest: stopping polling is not necessarily cancellation of a server job.
- Rate-limit expensive routes and validate settings on startup.
- Display condensed graph views for large snapshots. Rendering may be reduced, but analysis uses the complete accepted graph.

## 17. Acceptance tests — definition of done

### Functional

- A new user can register/sign in, create a project, reload, and still see the stored project.
- A second user cannot access that project's snapshots, reports or findings by guessing IDs.
- A valid supported CycloneDX input produces correct package identities, occurrences and edges.
- Malformed JSON, duplicate conflicting references, dangling edges and oversize files produce clear errors.
- Missing topology is flagged; advisory-only checks remain distinguishable from path analysis.
- Real OSV responses show source and time. Timeout gives partial/failed state, not “zero vulnerabilities.”
- Synthetic data is visibly labeled and never silently substituted into a real project.
- Every saved run can be retrieved after restart and exported with unchanged assumptions and numbers.

### Model invariants

- Lower index never exceeds upper; both remain between 0 and 100.
- Cycles terminate; disconnected assets are not counted; duplicate routes count each asset once.
- Versions and occurrence-specific graph paths remain distinct.
- Changing an unknown gate to false cannot increase the upper result for removal-only traversal.
- Runtime results are unchanged by the disable-install-scripts control.
- Install-only scenario respects each environment's installation and scripts policies.
- Witness paths reference real edges and correct gate provenance.
- Optimization stays within budget and evaluates combinations with parallel-route synergy.
- Repeat evaluation of the same graph/scenario/model version is deterministic.
- Incomplete graph warning survives export; it is not hidden by a narrow gate-based interval.

### Synthetic fixture

Create fictional packages and five application assets: Checkout weight 5, Billing 4, Admin 3, Docs 1, Identity 5. Total weight is 18. Design known runtime routes from `tiny-parse@1.0.0` to Checkout, Billing and Admin; an unknown route also reaches Docs; Identity is disconnected. Baseline lower is 12/18 = 66.7%; upper is 13/18 = 72.2%. Include a parallel-route case and budgeted controls. Mark gate values as fixture assumptions. Test expected values in backend and demo parity tests. Do not name real packages as malicious in the fixture.

### Quality targets, not claimed measurements

- Fixture evaluation completes within one second on a documented local test machine.
- Benchmark larger accepted graphs and disclose results; do not promise production-scale performance without measurement.
- Critical flows work in desktop Chromium; no uncaught console errors.
- Accessible labels, keyboard focus and tabular graph alternative are tested.
- CI runs type checks, unit/API tests and a focused end-to-end suite.

## 18. Antigravity implementation sequence

### Milestone 1 — Foundation and auth

Create the monorepo, environment examples, database migrations, Firebase client/server verification, project endpoints and protected dashboard. Implement public synthetic demo shell separately. Verify cross-user isolation before adding analysis.

### Milestone 2 — Real ingestion

Implement CycloneDX parser and identity/occurrence model with fixtures and failing-input tests. Connect upload UI to persisted snapshots. Do not enrich yet. Verify graph counts and topology warnings.

### Milestone 3 — Explainable model

Implement scenario schemas, tri-state gates, payload-specific policies, reachability, weighting and witness certificates. Add all model invariants and synthetic expected results. Build the graph workspace connected to API results.

### Milestone 4 — Mitigations and report

Implement control schema, edit validation, exact subset search, result comparison and JSON export. Test runtime/install distinction and parallel-route synergy. Keep original snapshots immutable.

### Milestone 5 — Real security evidence

Implement OSV adapter, fixtures/mocked contract tests, caching, partial-failure handling and findings UI. Test a live request only when network access is available, report its actual result, and never invent successful integration.

### Milestone 6 — Screening polish

Add readable onboarding, empty/error states, mobile-friendly layout, demo reset, keyboard support, README, architecture/model/security docs, and a 90-second walkthrough script. Run tests and report actual pass/fail status.

### Milestone 7 — Only after P0 is complete

Add package-lock v3 and GitHub import, criticality jobs, notifications and optional AI one at a time. Never replace the functioning P0 pipeline with a partially connected larger architecture.

## 19. Delivery checklist for the coding assistant

- Working source with locked dependencies, no pseudo-code standing in for core features.
- PostgreSQL migrations, fixture seeds and reproducible local commands.
- Firebase console setup guide and secrets guidance.
- Generated API contract and matching frontend calls.
- Tests, actual execution results and any remaining blockers.
- README clearly separating implemented, synthetic and planned features.
- `docs/IMPLEMENTATION_STATUS.md` updated after each milestone.
- No fabricated users, scan results, vulnerabilities, impact metrics or hosted URLs.
- No Firebase usage except Authentication and its local test emulator where configured.

## 20. Reference documentation for implementation

Consult official documentation when implementing provider calls; the links below are starting points, not a claim that integration is already implemented:

- Firebase ID token verification: https://firebase.google.com/docs/auth/admin/verify-id-tokens
- Firebase web authentication: https://firebase.google.com/docs/auth/web/start
- CycloneDX: https://cyclonedx.org/specification/overview/
- OSV API: https://google.github.io/osv.dev/api/
- deps.dev API: https://docs.deps.dev/api/v3/
- FastAPI: https://fastapi.tiangolo.com/
- NetworkX: https://networkx.org/documentation/stable/
- Cytoscape.js: https://js.cytoscape.org/
- Next.js: https://nextjs.org/docs

**Final product rule:** Make the app useful before making it elaborate. The differentiator is a working, evidence-backed explanation of downstream exposure and scenario-specific fixes—not the number of technologies in the architecture.
