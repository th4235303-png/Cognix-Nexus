# Cognix Core

Cognix Core is the Logixa Ecosystem research intelligence workspace.

## Flow

Research source → extraction → cleaning → Myanmar translation → summary → key points → fact-check flags → trust scoring → human review → approval → Google Drive export → Logixa Flow delivery.

## Structure

- `app/` — Next.js workspace UI
- `components/` — reusable UI and research workflow components
- `lib/` — mock data, typed API client, workflow types
- `backend/` — FastAPI boundary and Google Drive integration boundary

## Prototype safety

The current UI uses mock research data and mock export states. No Google OAuth credentials, refresh tokens, API keys, or provider secrets belong in the browser or repository.

## Backend contract

- `POST /sources`
- `GET /sources`
- `GET /sources/{id}`
- `GET /processing`
- `GET /processing/{id}`
- `GET /reviews`
- `POST /reviews/{id}/approve`
- `POST /reviews/{id}/revision`
- `POST /exports/google-drive`
- `GET /exports/{id}`
- `GET /activity`
- `GET /usage`

## Verification

Run frontend checks before merging:

```bash
npm run typecheck
npm run lint
npm run build
```
