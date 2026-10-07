# Cognix Nexus — Tools & Services

> Service catalog only. Live verification is tracked in PRODUCTION_STATUS.md.

## Production architecture

| Layer | Service | Verified state |
|---|---|---|
| Source / CI | GitHub + Actions | 🟢 Active; verified main CI #696 PASS |
| API | Render | 🟡 P0 security-hardening deploy in progress |
| Worker | Render | 🟡 P0 security-hardening deploy in progress |
| Database/Auth | Supabase | 🟢 Live |
| Vector | pgvector | 🟢 Enabled |
| Media | Cloudinary | 🟢 Live round-trip verified |
| Small artifacts | Supabase Storage | 🟡 Configured; full provider drill pending |
| Large originals | Backblaze B2 | 🟡 Configured; full provider drill pending |
| Export/backup | Google Drive | 🟡 Integration implemented; real OAuth/provider drill pending |
| LLM | OpenAI-compatible provider | ⚪ Intentionally deferred; not a current release gate |
| Frontend | Netlify | 🟡 Release activation/polish pending |
| Monitoring | Sentry | 🟡 Code hook exists; live ingestion unverified |
| Uptime / analytics | UptimeRobot / Umami / Axiom | 🟡 Live account evidence not verified |
| Edge | Cloudflare | 🟡 Account exists; Cognix zone/edge deployment needs a domain |
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

## Provider ownership

- Cloudinary: research media and image assets.
- Supabase Storage: small private artifacts.
- Backblaze B2: large original files.
- Google Drive: user-owned export/backup destination; integration exists, credentials/OAuth drill pending.
- LLM: optional provider-dependent intelligence; currently deferred.
- Supabase Auth: authentication and account controls.
- Render: API and worker runtime.
- Netlify: frontend hosting, activation pending final UI smoke.
- GitHub Actions: regression and release gates.
- Cloudflare: future edge/WAF once a Cognix domain is available.

## Planned infrastructure

These remain optional backlog items, not current production dependencies:
- Upstash Redis / rate-limit/cache
- PostHog
- Doppler/Infisical
- k6/Artillery
- Better Stack
- Mintlify/Docusaurus
- Cloudflare WAF after a Cognix domain/zone is available
- R2, dedicated vector DB, dedicated search engine, workflow orchestrator and Stream only when scale/product requirements justify them.

## Account-status rule

An account existing is not the same as a provider being production-verified. Use PRODUCTION_STATUS.md for evidence.

## Change policy

All service/configuration changes that are part of Cognix completion are recorded on main. Provider credentials remain external secrets and must never be committed.