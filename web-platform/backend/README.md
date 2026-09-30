# Cognix Core API

FastAPI boundary for source ingestion, processing, human review, approved knowledge, activity, usage, and Google Drive export.

The prototype uses an in-memory store so the frontend contract can be exercised end-to-end. Data resets when the process restarts.

## Safeguards

- URL validation and duplicate source detection
- Explicit processing state machine
- Retry counter and activity events
- Separate source trust and claim-review fields
- Critical-warning approval gate
- Approved-only Google Drive export
- Export idempotency keys
- No browser-side Google credentials
- Configurable CORS origins

## Run

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs are available at `/docs`; health is available at `/health`.

## Configuration

Copy `.env.example` to your deployment environment and set `COGNIX_CORS_ORIGINS` to a comma-separated list of trusted frontend origins. Do not commit credentials or tokens.

## Test

```bash
python -m unittest discover -s tests
```

## Production next steps

- PostgreSQL-backed repository and durable migrations
- Authentication and authorization
- Background workers and durable job queues
- Real extraction and translation providers
- Google OAuth 2.0 with backend-only secret storage
- Retry scheduling with bounded backoff
- Durable audit logs and request IDs
- Observability, rate limits, and structured error responses
