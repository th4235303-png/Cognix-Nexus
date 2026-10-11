# Provider setup (Cognix Nexus)

> Last reviewed: 2026-10-11

This guide matches the provider-key-only routing in `app/services/llm.py` and `app/services/embeddings.py`. Provider endpoints and model IDs are code-defined. Render stores provider credentials plus normal application/integration configuration; do not add model-ID or endpoint-URL overrides.

A configured key makes a route eligible; it does **not** prove that the key is valid, that the account has quota, or that the provider currently serves the model. Real provider E2E is required for a production PASS.

## LLM provider keys and code defaults

| Provider | Render key(s) | Model ID in code | Notes |
| --- | --- | --- | --- |
| Gemini | `GEMINI_API_KEY` | `gemini-2.5-flash` | Optional route. Check project/API enablement and model entitlement if the request fails. |
| OpenRouter | `OPENROUTER_API_KEY` | `openrouter/free` | Provider-side free-model routing/availability may change. |
| Hugging Face | `HUGGINGFACE_API_KEY` | `Qwen/Qwen2.5-7B-Instruct` | Keep the route/key as requested; inference credit and provider availability are account-dependent. |
| Mistral | `MISTRAL_API_KEY` | `ministral-8b-latest` | Check workspace entitlement, rate limits and quota. |
| Cohere | `COHERE_API_KEY` | `command-a-03-2025` | Required for the current AI release-gate preflight because it is also the compatible production embedding route. |
| Groq | `GROQ_API_KEY` | `qwen/qwen3.8-27b` | Code default; verify live model availability with provider E2E. |
| Cloudflare Workers AI | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | `@cf/meta/llama-3.1-8b-instruct` | Both values are needed to construct the account-scoped endpoint. |

`VOYAGE_API_KEY` is an embedding-provider credential, not an LLM route in the current router.

## Embedding dimension compatibility — important

The persisted PostgreSQL/pgvector schema is `vector(1536)`. The current embedding code keeps `VECTOR_DIMENSION = 1536`, and **Cohere `embed-v4.0` is currently the only configured embedding route that supports that persisted dimension**.

| Embedding provider | Model in code | Supported dimensions declared in code | Current production route? |
| --- | --- | --- | --- |
| Cohere | `embed-v4.0` | 256, 512, 768, 1024, 1536, 2048 | Yes — compatible at 1536 |
| OpenRouter | `liquid/lfm-2.5-embedding-350m:free` | 1024 | No — incompatible with persisted 1536 |
| Voyage | `voyage-4` | 256, 512, 1024, 2048 | No — incompatible with persisted 1536 |
| Cloudflare Workers AI | `@cf/baai/bge-large-en-v1.5` | 1024 | No — incompatible with persisted 1536 |

Do not change the database dimension or force a 1024-dimensional vector into a `vector(1536)` column. Enabling another production embedding route requires an approved schema migration, a re-embedding/backfill plan, and retrieval acceptance tests. Merely setting that provider key will not enable it at the current production dimension.

## Environment configuration

- Set provider keys only on the backend Render services that need them and in GitHub Actions repository secrets required by the release-gate workflow.
- Never put provider keys in frontend/Netlify `NEXT_PUBLIC_*` variables.
- Do not configure `COHERE_MODEL`, `GEMINI_MODEL`, `GROQ_MODEL`, `MISTRAL_MODEL`, other provider `*_MODEL` variables, provider `*_API_URL` overrides, or legacy `COGNIX_AI_*` / `COGNIX_LLM_*` / `COGNIX_EMBEDDING_*` overrides for the current router.
- Keep database, authentication/JWKS, CORS/host allowlists, storage, Google Drive, Sentry, E2E, recovery, and release-gate variables. They serve other parts of the system and are not obsolete just because they are not LLM model settings.
- Optional LLM provider keys can be absent. The release-gate preflight currently requires `COHERE_API_KEY` for the AI provider/embedding gate; other listed provider keys are optional unless a particular drill explicitly tests them.
- The repository blueprint is not proof of the live Render environment. Compare live variable names and service settings before cleanup; delete only names confirmed present and unused.

## Cloudflare: token and account ID

1. In Cloudflare Dashboard, open Account API Tokens and create a custom token scoped to the account that owns Workers AI.
2. Grant the Workers AI permission required for inference; do not use a Global API Key.
3. Store the generated token as `CLOUDFLARE_API_TOKEN`.
4. Store the account ID as `CLOUDFLARE_ACCOUNT_ID`.
5. Add both only to backend services and the relevant GitHub Actions secret store.
6. Run the real provider E2E and inspect provider usage/errors before calling the route verified.

A 401 commonly points to token/account pairing or permissions; quota/entitlement errors require checking the account's current allocation and provider dashboard.

## Google Drive refresh-token recovery

A failed live drill previously reported `GoogleOAuthRefreshTokenExpiredOrRevoked`. The presence of `GOOGLE_REFRESH_TOKEN` only proves a value is configured; it does not prove that the token remains valid. The account owner must re-authorize, obtain a fresh refresh token, replace it in the appropriate backend/CI secret stores, redeploy if needed, then rerun the export/idempotency drill. Never paste the token into chat or commit it.

## Failure triage

- HTTP 401/403: check key validity, account/project entitlement and permissions.
- HTTP 402: check provider credit/billing/quota; changing the model or rotating a key does not create new credit.
- HTTP 429: check rate limits and retry policy.
- Model-not-found/unsupported: compare the code-defined model ID against the provider's current model catalog; update code and tests through review rather than adding a Render model override.
- Embedding dimension mismatch: stop the operation; do not bypass the 1536-dimension guard.

## Official references

- Hugging Face Inference Providers pricing: https://huggingface.co/docs/inference-providers/pricing
- Hugging Face chat completion/model routing: https://huggingface.co/docs/inference-providers/tasks/chat-completion
- Mistral Studio API key quickstart: https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key
- Cloudflare Workers AI pricing/free allocation: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Cloudflare API token permissions: https://developers.cloudflare.com/fundamentals/api/reference/permissions/
