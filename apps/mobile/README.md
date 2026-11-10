# Cognix Brain Vault Mobile

Expo / React Native client for Cognix Nexus.

## Current behavior

- Supabase email/password sign-in with a persisted auth session in Expo SecureStore.
- Cognix API calls use the authenticated Supabase access token as a Bearer token.
- Quick captures are persisted by the backend or retained in a capped, per-account local SecureStore queue when the API rejects/fails. The idempotency key protects retries against duplicate note creation.
- Generate flashcards from a saved Brain Vault note and persist owner-scoped SM-2 review intervals and due dates in PostgreSQL.
- Secret Vault supports short private records stored locally using OS SecureStore encryption. Records, PIN verifier, and lockout state are scoped per authenticated account; secret records are not synced to the backend. The PIN is an extra local UI gate, not the encryption key.

## Configuration

Copy `.env.example` to `.env` and set these public client configuration values:

- `EXPO_PUBLIC_COGNIX_API_URL`: Cognix API base URL.
- `EXPO_PUBLIC_SUPABASE_URL`: Supabase project URL.
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`: Supabase publishable/anon key (never a service-role key).

Sign in with an existing Supabase email/password account. The Cognix backend must be configured to validate Supabase bearer tokens and map the authenticated subject to that owner's data.

## Quick Start

```bash
cd apps/mobile
npm install
npm run typecheck
npm run start
```
