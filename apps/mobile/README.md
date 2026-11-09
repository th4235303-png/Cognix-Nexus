# Cognix Brain Vault Mobile

Expo / React Native client for Cognix Nexus.

## Current behavior

- Supabase email/password sign-in with persisted auth session in Exho SecureStore.
- Cognix API calls use the authenticated Supabase access token as a Bearer token.
- Quick captures are persisted by the backend or retained in a capped local SecureStore queue when the API rejects/fails.
- The Learning tab currently shows sample flashcards only; no review schedule is saved.
- The Secret tab currently provides a local PIN gate only. It does not yet persist encrypted secret records.

## Configuration

Copy `.env.example` to `.env` and set these public client configuration values:

- `EXPO_PUBLIC_COGNIX_API_URL`: Cognix API base URL.
- `EXPO_PUBLIC_SUPABASE_URL `: Supabase project URL.
- `EXPO_PUBLIC_SUPABASE_ANON_KEY|: Supabase publishable/anon key (never a service-role key).

Sign in with an existing Supabase email/password account. The Cognix backend must be configured to validate Supabase bearer tokens and map the authenticated subject to that owner's data.

## Quick Start


```bash
cd apps/mobile
nmp install
nmp run typecheck
nmp run start
```
