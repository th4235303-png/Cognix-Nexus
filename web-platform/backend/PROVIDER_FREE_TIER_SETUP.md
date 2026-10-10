# Free-tier provider setup (Cognix Nexus)

This guide separates API credentials from model IDs. Model selection does not grant free usage or restore exhausted credits.

## Environment variables

Set these as server-side environment variables in Render (backend service) and as GitHub Actions repository secrets for the Release Gates workflow. Never commit values or paste them into issues/chat.

| Provider | Required variable | Model default in code | Free-use caveat |
| --- | --- | --- | --- |
| Gemini | `GEMINI_API_KEY` | `gemini-3.8-flash` | HTTP 403 requires checking API key access, project/API enablement, and model entitlement; the model ID is listed in Google model docs. |
| Hugging Face | `HUGGINGFACE_API_KEY` | `openai/gpt-oss-120b:cheapest` | Free accounts have a small monthly Inference Providers credit allowance (currently $0.10, subject to change). HTTP 402 after that means credits/usage entitlement, not a bad model name. HTTP 400 requires inspecting the provider response/request/model routing. This default uses Hugging Face’s documented `:cheapest` provider-selection policy; it is credit-based and not guaranteed to be free indefinitely. |
| Mistral | `MISTRAL_API_KEY` | `mistral-small-latest` | Mistral Studio has a limited Free mode. Create an API key in Studio and verify the workspace is in Free mode. HTTP 403 means key/workspace/model entitlement needs checking; HTTP 429 indicates rate limiting or quota exhaustion and should be retried after the provider limit resets. |
| Cloudflare Workers AI | `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` | `@cf/meta/llama-3.1-8b-instruct-fp8-fast` | Workers AI includes 10,000 neurons/day at no charge. The old GLM-5.2 default requires paid Workers or AI Gateway credits. |
| Cloudflare embeddings | Same Cloudflare variables | `@cf/baai/bge-large-en-v1.5` | Multilingual embeddings; current Cognix 1024-dimension route supports it. |

## Hugging Face model selection notes

- Recommended default for the current OpenAI-compatible route: `openai/gpt-oss-120b:cheapest`. Hugging Face documents the model and the `:cheapest` routing suffix. This is **not a promise of zero-cost inference**; the free account allowance is limited credit and provider availability/pricing can change.
- `zai-org/GLM-5.3-Flash` exists as a Hugging Face model repository, but repository existence alone does not prove that an Inference Provider currently serves it for this account. Confirm it appears in the Inference Providers catalog before using it as a runtime default.
- `Qwen/Qwen3.8-27B` could not be verified as an exact official model ID during this audit. Do not configure that spelling until the exact model page and provider support are confirmed.

## Embedding dimension compatibility

The release probe explicitly tests 1024-dimensional routes. Cloudflare Workers AI documents `@cf/baai/bge-large-en-v1.5` as a 1024-dimensional embedding model. However, the current production embedding default and persisted vector column are 1536-dimensional. Do not change the production dimension to 1024 without a coordinated database migration/re-embedding plan; a 1024-vector cannot be stored in a `vector(1536)` column.

## Cloudflare: exactly what goes where

1. Open Cloudflare Dashboard → Manage Account → Account API tokens (or My Profile → API Tokens, depending on dashboard layout) → Create Token.
2. Create a custom token scoped to the Cloudflare account that owns Workers AI. Grant Account → Workers AI → Edit permission (Cloudflare's API token permission label; this is the permission used for Workers AI inference). Do not use a Global API Key.
3. Copy the generated token once. Store it as `CLOUDFLARE_API_TOKEN`.
4. In the same Cloudflare account, find the account ID on the account overview page and store it as `CLOUDFLARE_ACCOUNT_ID`. This is an ID, not a secret/token.
5. Add both values to Render → backend service → Environment and GitHub → Cognix-Nexus → Settings → Secrets and variables → Actions using those exact names.
6. Redeploy/restart the Render backend after changing environment variables. Re-run the Release Gates workflow.
7. Monitor Workers AI → Usage. The free allocation resets daily at 00:00 UTC. A 401 usually means the token/account pairing or permissions are wrong; 402 generally indicates billing/credits/entitlement.

## Google Drive refresh-token recovery

A failed live drill reported `GoogleOAuthRefreshTokenExpiredOrRevoked`. The presence of `GOOGLE_REFRESH_TOKEN` in GitHub Actions only proves the secret is set; it does not prove the token is still valid. Re-authorize using the backend Google Drive authorization endpoint, obtain a fresh refresh token, replace the `GOOGLE_REFRESH_TOKEN` secret in GitHub Actions and the Render backend environment, redeploy the backend, and rerun the Drive export/idempotency drill. Never paste the token into chat or commit it.

## Where to put credentials

- GitHub Actions: repository → Settings → Secrets and variables → Actions → New repository secret. Add each provider key under the exact variable name above.
- Render backend: service → Environment → add the same variable names. Save and redeploy.
- Do not put provider secrets in frontend/Netlify `NEXT_PUBLIC_*` variables. These keys must remain backend-only.
- If the provider's free allowance has expired or been exhausted, rotating the key or changing model IDs will not create new credits. Check the provider dashboard before deciding to upgrade/pay.

## Official references

- Hugging Face Inference Providers pricing: https://huggingface.co/docs/inference-providers/pricing
- Hugging Face chat completion/model routing: https://huggingface.co/docs/inference-providers/tasks/chat-completion
- Mistral Studio API key quickstart: https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key
- Cloudflare Workers AI pricing/free allocation: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Cloudflare API token permissions: https://developers.cloudflare.com/fundamentals/api/reference/permissions/
