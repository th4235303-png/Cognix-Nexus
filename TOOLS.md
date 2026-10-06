# Cognix Nexus — Tools & Services

> Service catalog only. Live verification is tracked in PRODUCTION_STATUS.md.

## Production architecture

| Layer | Service | Verified state |
|---|---|---|
| Source / CI | GitHub + Actions | 🟢 Active; main CI #696 PASS |
| API | Render | 🟡 Live; deploy revision must be refreshed to latest main |
| Worker | Render | 🟡 Live; latest main revision must be refreshed |
| Database/Auth | Supabase | 🟢 Live |
| Vector | pgvector | 🟢 Enabled |
| Media | Cloudinary | 🟢 Live round-trip verified |
| Small artifacts | Supabase Storage | 🟡 Configured; full E2E pending |
| Large originals | Backblaze B2 | 🟡 Configured; full E2E pending |
| Export/backup | Google Drive | 🔴 OAuth/provider E2E blocked |
| LLM | OpenAI-compatible provider | 🔴 Live provider drill blocked by 402/config |
| Frontend | Netlify | 🟡 Intentionally paused |
| Monitoring | Sentry | 🟡 Code hook exists; live ingestion unverified |
| Uptime / analytics | UptimeRobot / Umami / Axiom | 🟡 Account/configuration claims require live evidence |
| Edge | Cloudflare | 🟡 Account exists; Cognix zone/edge deployment not verified |
| Email | Brevo | 🟡 Integration exists; live send not verified |
| Queue | Upstash QStash | 🟡 Integration exists; live delivery not verified |
| Mobile | Expo/EAS | 🟡 Foundation exists; device/EAS production verification pending |

## Storage rules

| File role | Provider | Rule |
|---|---|---|
| Research images/covers/thumbnails | Cloudinary | <10 MB |
| Small PDFs/notes/summaries | Supabase Storage | <=50 MB, private |
| Large PDFs/EPUBs/research papers | Backblaze B2 | >50 MB |
| Export packages/backups | Google Drive | user-owned destination |

## Planned infrastructure

These remain optional backlog items, not current production dependencies:
- Upstash Redis / rate-limit/cache
- PostHog
- Doppler/Infisical
- Playwright
- k6/Artillery
- Better Stack
- Mintlify/Docusaurus
- Cloudflare WAF after a Cognix domain/zone is available
- R2, dedicated vector DB, dedicated search engine, workflow orchestrator and Stream only when scale/product requirements justify them.

## Account-status rule

An account existing is not the same as a provider being production-verified. Use PRODUCTION_STATUS.md for evidence.