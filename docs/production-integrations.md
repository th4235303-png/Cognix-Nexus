# Cognix Core production integration map

Cognix Core is intentionally runnable locally before any provider accounts are connected.

## Runtime map

| Service | Role | Prototype | Production |
| --- | --- | --- | --- |
| GitHub | source + CI | connected | connected |
| Vercel | Next.js frontend | not required | preferred Next.js host; connect repo and set `NEXT_PUBLIC_COGNIX_API_URL` |
| Netlify | Next.js frontend | not required | supported fallback; use the existing `netlify.toml` and set `NEXT_PUBLIC_COGNIX_API_URL` |\n| Render (or equivalent) | FastAPI backend | localhost:8000 | deploy `backend/` and set CORS |
| Supabase | PostgreSQL/auth/storage option | not required | provision PostgreSQL first; add auth/storage only if adopted |
| Sentry | error monitoring | not required | add DSNs/SDKs after production runtime exists |
| Google Cloud/Drive | approved knowledge export | mock boundary | OAuth 2.0 + Drive API, backend-only secrets |
| Logixa Flow | downstream delivery | UI placeholder | connect webhook/API after approval/export contracts stabilize |

## Environment variables

### Frontend
- `NEXT_PUBLIC_COGNIX_API_URL`

### Backend
- `COGNIX_CORS_ORIGINS`
- future Google OAuth/Drive secrets must be backend-only
- future database URL must be backend-only
- future Sentry DSN must be backend-only unless an SDK explicitly requires a public DSN

Never commit real values to Git.

## Recommended production order

1. Deploy FastAPI to Render (or another managed backend host).
2. Provision Supabase PostgreSQL and migrate the in-memory store.
3. Deploy Next.js to Vercel and set `NEXT_PUBLIC_COGNIX_API_URL`. If Vercel access is unavailable, deploy the same frontend to Netlify; no application rewrite is required.
4. Add Sentry to frontend/backend and verify error events.
5. Configure Google Cloud OAuth 2.0 and Drive permissions; keep credentials server-side.
6. Connect Logixa Flow after the approved/exported event contract is stable.
7. Add background workers, rate limits, authentication/authorization, and durable audit logging.

The repository includes both Vercel and Netlify deployment boundaries. Vercel is the preferred Next.js hosting path for this project, while Netlify is a supported fallback. Provider accounts and production secrets are deliberately not created by code.
