# Cognix Core production integration map

## Runtime map

| Service | Role | Local | Production |
| --- | --- | --- | --- |
| GitHub | source + CI | connected | connected |
| Netlify | Next.js frontend | optional | primary frontend host |
| Render | FastAPI API + worker | optional | primary backend host |
| Supabase | PostgreSQL + Auth | optional | managed persistence/auth |
| Sentry | observability | optional | recommended |
| Google Drive | approved knowledge delivery | mock provider | OAuth 2.0 + Drive API |

## Repository layout

Deployable applications live under web-platform/frontend and web-platform/backend. The root netlify.toml points Netlify at the frontend base directory; render.yaml points both Render services at the backend directory.

## Environment variables

Frontend: NEXT_PUBLIC_COGNIX_API_URL, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY.

Backend: COGNIX_CORS_ORIGINS, COGNIX_ALLOWED_HOSTS, COGNIX_RATE_LIMIT_PER_MINUTE, DATABASE_URL, COGNIX_AUTH_REQUIRED, COGNIX_JWT_JWKS_URL, issuer/audience settings, AI provider settings, Google OAuth settings, and optional Sentry settings.

Provider secrets are backend-only. Never expose GOOGLE_REFRESH_TOKEN or AI API keys to the browser.

## Production sequence

1. Provision PostgreSQL and set DATABASE_URL.
2. Deploy the API and worker on Render from web-platform/backend.
3. Deploy the frontend on Netlify using the root netlify.toml and set public API/Supabase settings.
4. Configure Supabase Auth and the backend JWKS issuer/audience.
5. Configure the AI provider and model.
6. Configure Google Cloud OAuth/Drive access through the backend authorization endpoint; do not paste refresh tokens into frontend code or browser-visible pages.
7. Set trusted CORS and host values and verify /health and /ready.
8. Enable Sentry if desired and verify error events.

Mock processing and mock Drive providers remain available for local development. Production should use configured AI and Google providers.
