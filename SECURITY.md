# Security Policy

> Owner: Security
> Update when: threat model, trust boundaries, security controls, account limitations, or release security gates change
> Last Updated: 2026-10-08
> Do NOT put here: general architecture, product roadmap, or detailed operational runbooks.

## Scope
Cognix Nexus handles personal knowledge, research sources, user-owned records, encrypted vault material and provider credentials. Security controls span browser, API, worker, database and provider boundaries.

## Threat model / principles
- Authentication fails closed in production.
- User-owned records are owner-scoped.
- RLS is deny-by-default where direct client access is not intended.
- AI output is never silently promoted to canonical truth.
- Secrets stay backend-only.
- Vault plaintext remains client-side.
- Outbound fetching validates scheme, destination and redirects to mitigate SSRF.
- Worker jobs use durable leases/fencing and bounded retries.
- Durable data does not silently fall back to in-memory persistence.
- Provider failures are explicit.

## Secret Vault cryptography
The current implementation uses **PBKDF2-SHA256 with 600,000 iterations** to derive a 256-bit AES-GCM key in the browser. Evidence checked 2026-10-08 in `web-platform/frontend/app/vault/page.tsx`. The historical Argon2id statement is a future/target design claim and is not the current implementation.

## Durable security decisions
### ADR-003 — Owner isolation
Owner-scoped RLS/persistence context protects user data; legacy ownerless records fail closed.

### ADR-005 — SSRF defense in depth
Validate URL scheme/destination and every redirect, then use validated transport.

### ADR-009 — Free-tier Auth limitation
Supabase currently reports leaked-password protection disabled because the active project is on the free tier. Treat this as an account-plan limitation, not an application-code defect, and keep the warning visible.

## Production security gates
- Supabase RLS and owner-isolation tests.
- SSRF regression tests.
- Dependency audit and secret scanning in CI.
- Backup/restore safety guard.
- Auth/JWKS verification.
- CORS/host allow-listing.
- Upload size/type controls.
- Provider fail-closed behavior.

## Secrets
Never commit provider credentials, OAuth refresh tokens, database secrets or API keys. Provider credentials remain backend-only.

## Incident boundary
Do not publish secrets, exploit details or user data in public issues. Do not test destructive actions against production data.

## Release support
Only the current main production release and the immediately preceding known-good release are supported unless a release note says otherwise.
