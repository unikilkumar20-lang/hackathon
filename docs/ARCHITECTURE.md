# RippleGuard Architecture Specification

## 1. System Overview

RippleGuard is a modular monolith designed for explainable dependency risk and compromise scenario analysis.

```
+-------------------------------------------------------------+
|                      Next.js Frontend                        |
|  - React 18, TypeScript, Tailwind CSS, Lucide               |
|  - Cytoscape.js + ELK layout engine                         |
|  - Firebase Client SDK (Email/Password & Google Sign-In)   |
+-------------------------------------------------------------+
                               |
                Authorization: Bearer <ID_TOKEN>
                               v
+-------------------------------------------------------------+
|                       FastAPI Backend                       |
|  - Token verification via Firebase Admin (fails closed)     |
|  - User upsert & explicit owner_user_id scoping             |
|  - Project & Asset CRUD                                     |
|  - NetworkX Graph Traversal & Tri-State Gate Evaluation    |
|  - Combinatorial Counterfactual Mitigation Engine           |
|  - Real OSV Enrichment Client with cache & timestamping    |
+-------------------------------------------------------------+
                               |
                   PostgreSQL / SQLAlchemy 2.0
                               v
+-------------------------------------------------------------+
|                     PostgreSQL Database                     |
|  - users, projects, assets, snapshots, inventories          |
|  - package_identities, occurrences, edges, snapshot_assets  |
|  - enrichment_checks, advisories, findings, evidence        |
|  - runs, controls, optimization_runs                        |
+-------------------------------------------------------------+
```

## 2. Mandatory Architecture Decisions

1. **Authentication Only:** Firebase Authentication is used strictly for identity. PostgreSQL stores all application data. Firestore, Realtime Database, Firebase Storage, and Firebase Functions are forbidden.
2. **Fail-Closed Protected Endpoints:** Protected API endpoints return HTTP 401 if Firebase credentials are unset or the token is invalid.
3. **Data Isolation:** Every project is scoped to the verified `owner_user_id`. Queries for foreign or nonexistent projects return HTTP 404 to avoid leaking metadata.
4. **Distinct Package vs. Occurrence Identity:** Graph traversal operates over *occurrences* (specific to snapshot and application asset), preserving duplicate versions and distinct resolution paths.
