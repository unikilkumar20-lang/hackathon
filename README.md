# RippleGuard

> **Simulate the ripple. Prioritize the repair.**

RippleGuard is an explainable open-source dependency risk and compromise-scenario analysis web application. It accepts software bill of materials (CycloneDX JSON), identifies known security advisories via OSV, maps multi-application dependency relationships, and simulates downstream blast-radius exposure if a selected package were compromised.

---

## Tech Stack

- **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS, Lucide Icons, Cytoscape.js + ELK
- **Backend**: Python, FastAPI, Pydantic v2, NetworkX
- **Database**: PostgreSQL, SQLAlchemy 2.0, Alembic
- **Authentication**: Firebase Authentication ONLY (Client SDK + Admin Token Verification)
- **Local Infrastructure**: Docker Compose

---

## Architectural Constraints & Invariants

- **Firebase is used ONLY for authentication.** PostgreSQL persists all application data.
- **Fail-closed security:** Missing Firebase configurations or invalid tokens reject requests with HTTP 401.
- **Real vs. Synthetic Isolation:** The public `/demo` sandbox runs entirely from a static synthetic fixture and cannot read/mutate private projects.
- **Never execute dependencies:** Never run install scripts or execute untrusted code from uploaded packages.

---

## Quickstart

### 1. Backend Service (`services/api`)

```bash
cd services/api

# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Configure environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Run tests
pytest -v

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Application (`apps/web`)

```bash
cd apps/web

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Run TypeScript type check
npm run typecheck

# Start development server
npm run dev
```

### 3. Local Docker Runner (`infra`)

```bash
cd infra
docker compose up -d
```

---

## Milestones Roadmap

1. **Milestone 1 (Complete)**: Project foundation, Firebase sign-in, backend token verification, PostgreSQL models, project/asset CRUD with ownership isolation.
2. **Milestone 2**: CycloneDX JSON upload, validation, immutable snapshots and dependency graph.
3. **Milestone 3**: Runtime/install-script scenarios, tri-state gates, weighted exposure and explainable paths.
4. **Milestone 4**: Budget-constrained mitigation comparison and JSON reports.
5. **Milestone 5**: Real OSV vulnerability checks with evidence, timestamps and honest failure states.
6. **Milestone 6**: Accessible UI, public synthetic demo, integration tests and setup documentation.
