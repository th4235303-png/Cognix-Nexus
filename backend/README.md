# Cognix Core API

FastAPI boundary for source ingestion, processing, human review, approved knowledge, activity, usage, and Google Drive export.

The current implementation is a safe prototype: endpoints return mock state and the Google Drive service is only an integration boundary.

Run locally:

```bash
cd backend
uvicorn app.main:app --reload
```

Production requirements:
- OAuth 2.0 for private Google Drive access.
- Secrets in environment variables or a secret manager.
- Idempotency for export requests.
- Retry/pending states for Drive outages.
- Persisted audit events.
- Authentication/authorization before exposing write endpoints.
