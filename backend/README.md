# Cognix Core API

FastAPI boundary for source ingestion, processing, human review, approved knowledge, activity, usage, and Google Drive export.

The prototype uses an in-memory store so the frontend contract can be exercised end-to-end. Data resets when the process restarts.

Safeguards include duplicate URL detection, source validation, approval gating, approved-only export, export idempotency, activity events, and safe Drive package metadata.

Run:
```bash
cd backend
uvicorn app.main:app --reload
```

Test:
```bash
python -m unittest discover -s tests
```

Production next steps: PostgreSQL, authentication/authorization, background workers, real extraction/translation providers, Google OAuth 2.0, retry scheduling, and durable audit logs.
