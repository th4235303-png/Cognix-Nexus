# Cognix Core

Cognix Core is a private research intelligence workspace in the Logixa Ecosystem.

## Architecture

- **Frontend:** Next.js + React + TypeScript + Tailwind CSS
- **Backend:** FastAPI + Python
- **Database:** PostgreSQL / Supabase
- **Authentication:** Supabase Auth + backend JWT verification
- **Processing:** Python worker and research-processing services
- **Delivery:** Google Drive only
- **Hosting:** Netlify (frontend) + Render (API/worker)

Python is intentionally kept in `backend/` for the API, processing pipeline, background worker, persistence, and Google Drive integration. It is not a second frontend.

## Research flow

Research source → extraction → cleaning → Myanmar translation → summary → key points → fact-check flags → trust scoring → human review → approval → Google Drive export.

## Repository structure

```
app/                 Next.js routes and pages
components/          Shared UI and research workspace components
lib/                 Frontend API client, auth, types, and UI data
backend/             FastAPI API, worker, persistence, processing, Drive integration
backend/migrations/  PostgreSQL schema migrations
backend/tests/       Backend tests
docs/                Production integration documentation
.github/             CI workflow
```

## Production delivery

Approved research is packaged and uploaded to Google Drive as:

```
/cognix-core/
  /YYYY-MM-DD/
    /research-id/
      source.json
      original-reference.txt
      summary.md
      myanmar-summary.md
      claims.json
      review.json
```

No Logixa Flow webhook is used.

## Local development

Frontend:

```bash
npm ci
npm run dev
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Verification

```bash
npm run typecheck
npm run lint
npm run build

cd backend
python -m compileall app
python -m unittest discover -s tests -v
```

Never commit API keys, OAuth refresh tokens, database passwords, or other provider secrets.
