# Cognix Core production integration map

Cognix Core is runnable locally before provider accounts are connected. The backend now supports durable PostgreSQL persistence when `DATABASE_URL` is configured; without it, local development keeps the in-memory prototype.

## Runtime map

| Service | Role | Prototype | Production |
| --- | --- | --- | --- |
| GitHub | source + CI | connected | connected |
| Vercel | Next.js frontend | not required | preferred Next.js host; connect repo and set `NEXT_PUBLIC_COGNIX_API_URL` |
| Netlify | Next.js frontend | not required | supported fallback; use the existing `netlify.toml` and set `NEXT_PUBLIC_COGNIX_API_URL` |
| Render (or equivalent) | FastAPI backend | localhost:8000 | deploy `backend/`, set CORS, and configure `DATABASE_URL` |
| Supabase | PostgreSQL/auth/storage option | not required | provision PostgreSQL and provide its connection string as `DATABASE_URL`; auth/storage can be added later |
| Sentry | error monitoring | not required | add DSNs/SDKs after production runtime exists |
| Google Cloud/Drive | approved knowledge export | mock boundary | OAuth 2.0 + Drive API, backend-only secrets |
| Logixa Flow | downstream delivery | UI placeholder | connect webhook/API after approval/export contracts stabilize |

## Environment variables

### Frontend
- `NEXT_PUBLIC_COGNIX_API_URL`

### Backend
- `COGNIX_CORS_ORIGINS`
- `DATABASE_URL`
- future Google OAuth/Drive secrets must be backend-only
- future Sentry DSN must be backend-only unless an SDK explicitly requires a public DSN

When `DATABASE_URL` is configured, the API initializes the version-controlled SQL migrations on startup and loads sources, processing tasks, reviews, claims, exports, and activity history from PostgreSQL. Without it, the API reports `memory-prototype` readiness mode.

Never commit real values to Git.

## Recommended production order

1. Provision PostgreSQL (Supabase is the planned managed option) and set `DATABASE_URL` on the backend.
2. Deploy the FastAPI web service and the separate processing worker on Render (or another managed backend host), sharing the same `DATABASE_URL`; set `COGNIX_CORS_ORIGINS` on the API and `COGNIX_WORKER_POLL_SECONDS` on the worker.
3. Deploy Next.js to Vercel and set `NEXT_PUBLIC_COGNIX_API_URL`. If Vercel access is unavailable, deploy the same frontend to Netlify; no application rewrite is required.
4. Add Sentry to frontend/backend and verify error events.
5. Configure Google Cloud OAuth 2.0 and Drive permissions; keep credentials server-side.
6. Connect Logixa Flow after the approved/exported event contract is stable.
7. Enable JWT authentication with a trusted issuer/secret or JWKS endpoint; keep `COGNIX_AUTH_REQUIRED=false` only for local prototype use. Supabase Auth can provide the browser session and JWKS-backed access tokens.\n8. Add rate limits, durable audit logging, and the remaining provider integrations.

The repository includes both Vercel and Netlify deployment boundaries. Provider accounts and production secrets are deliberately not created by code.
