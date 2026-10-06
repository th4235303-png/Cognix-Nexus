# Security Policy

## Scope

Cognix Nexus handles personal knowledge, research sources, user-owned records, encrypted vault material and provider credentials. Security controls are enforced at the browser, API, worker, database and provider boundaries.

## Security principles

- Authentication fails closed in production.
- User-owned records are owner-scoped.
- RLS is deny-by-default where direct client access is not intended.
- AI output is never silently promoted to canonical truth.
- Secrets stay backend-only.
- Vault plaintext remains client-side.
- Outbound fetching uses SSRF validation and redirect validation.
- Worker jobs use durable leases/fencing and bounded retries.
- Durable data must not silently fall back to in-memory persistence.
- Provider failures are explicit.

## Vulnerability reporting

Do not publish secrets, exploit details or user data in public issues.

For a private report, contact the repository owner through GitHub's private security reporting mechanism if enabled. If private reporting is unavailable, send a concise report through the project maintainer's private contact channel and include:
- affected component;
- reproduction steps;
- impact;
- suggested mitigation;
- whether user data or credentials may be exposed.

Do not test destructive actions against production data.

## Production security gates

- Supabase RLS and owner-isolation tests.
- SSRF regression tests.
- Dependency audit in CI.
- Secret-scan expectations.
- Backup/restore safety guard.
- Auth/JWKS verification.
- CORS/host allow-listing.
- Upload size/type controls.
- Provider fail-closed behavior.

## Known external action

Supabase currently reports leaked-password protection disabled. The active project is on the free tier, where this Auth feature cannot be enabled. Treat this as an account-plan limitation, keep the warning visible, and do not mislabel it as an application-code defect.

## Supported versions

Only the current main production release and the immediately preceding known-good release should be treated as supported unless a release note says otherwise.