# Cognix Core

Cognix Core is a research intelligence workspace for source ingestion, processing, human review, trust scoring, and approved Google Drive export.

## Platform architecture

- Frontend: Next.js + React + TypeScript + Tailwind CSS
- Backend: FastAPI + Python processing worker
- Persistence: PostgreSQL / Supabase
- Authentication: Supabase Auth with backend JWT verification
- Delivery: Google Drive only
- Hosting: Netlify (frontend) + Render (API/worker)

Next.js and Python are intentionally separate applications under the web-platform directory.

## Repository structure

web-platform/
├── frontend/   Next.js application
├── backend/    FastAPI API, worker, migrations, tests
└── docs/       Architecture, deployment and operations docs

.github/        CI
README.md       Project overview
SECURITY.md     Security policy

## Research lifecycle

New → Queued → Extracting → Cleaning → Translating → Summarizing → Key Points → Fact-check Flagging → Trust Scoring → Needs Review → Approved → Drive Exported

Human-edited Myanmar translation and critical fact-check warnings are preserved separately from AI-derived content. Approval blocks when critical warnings remain unresolved or when an approved Myanmar translation is missing.

## Google Drive output

/cognix-core/YYYY-MM-DD/research-id/
├── source.json
├── original-reference.txt
├── summary.md
├── myanmar-summary.md
├── claims.json
└── review.json

No Logixa Flow webhook is used.

## Local development

Frontend:

    cd web-platform/frontend
    npm ci
    npm run dev

Backend:

    cd web-platform/backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

## Verification

    cd web-platform/frontend
    npm run typecheck
    npm run lint
    npm run build

    cd ../backend
    python -m compileall app
    python -m unittest discover -s tests -v

Never commit API keys, OAuth refresh tokens, database passwords, or other provider secrets.
