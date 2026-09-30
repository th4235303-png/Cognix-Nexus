# Cognix Core API

FastAPI boundary for source ingestion, processing, human review, approved knowledge, activity, usage, and Google Drive export.

## Runtime modes

- Local: in-memory persistence is available for development and tests.
- Production: PostgreSQL persistence is enabled when DATABASE_URL is configured and migrations are applied automatically at startup.
- Worker: python -m app.worker advances queued processing tasks against the shared database.

## Safeguards

- Public HTTP(S) source validation with SSRF protections
- Duplicate source detection
- Explicit processing state machine and retry handling
- Separate source trust and claim confidence
- Critical-warning approval gate
- Approved-only Google Drive export
- Database-backed export idempotency
- Backend-only Google credentials
- CORS, trusted-host, JWT authentication, request IDs, rate limiting, and optional Sentry

## Run

    python -m pip install -r requirements.txt
    uvicorn app.main:app --reload

API docs are available at /docs; health is available at /health; readiness is available at /ready.

## Production configuration

Set DATABASE_URL, authentication/JWKS settings, AI provider settings, Google Drive settings, and trusted frontend origins through the hosting provider secret manager. Keep COGNIX_AUTH_REQUIRED=false only for local development.

The Google OAuth callback never renders the refresh token. The resulting credential must be stored securely as GOOGLE_REFRESH_TOKEN on the backend.

## Test

    python -m unittest discover -s tests -v
