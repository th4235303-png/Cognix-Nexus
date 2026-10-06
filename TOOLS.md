# Cognix Nexus — Tools & Services

> **Stack reference.**
> See `REMAINING_WORK.md` for task tracking.
> See `UI_PLAN.md` for frontend planning.

---

## Current Stack (Production)

| Layer | Service | Status |
|---|---|---|
| Frontend | Netlify | ⚠️ Paused |
| Backend API | Render (FastAPI) | ✅ Live |
| Backend Worker | Render | ✅ Live |
| Database | Supabase PostgreSQL | ✅ Live |
| Vector DB | pgvector | ✅ Live |
| Auth | Supabase Auth | ✅ Live |
| Storage | Cloudinary | ✅ Live |
| Storage | Supabase Storage | ✅ Live |
| Storage | Backblaze B2 | ✅ Live |
| Export | Google Drive | ✅ Live |
| Edge / AI | Cloudflare Workers | ✅ Live |
| Edge / AI | Cloudflare AI Gateway | ✅ Live |
| Monitoring | Sentry | ✅ Live |
| Monitoring | UptimeRobot | ✅ Live |
| Monitoring | Umami Cloud | ✅ Live |
| Monitoring | Axiom | ✅ Live |
| Email | Brevo | ✅ Live |
| Queue | QStash | ✅ Live |
| CI/CD | GitHub Actions | ✅ Live |
| Mobile | Expo | ✅ Foundation |
| AI Provider | OpenAI-compatible LLM | ⚠️ 402 |

---

## Storage Tier Rules

| File type | Provider | Rule |
|---|---|---|
| Research images, covers, thumbnails | Cloudinary | <10 MB |
| Small PDFs, notes, summaries | Supabase Storage | ≤50 MB, private |
| Large PDFs, EPUBs, research papers | Backblaze B2 | >50 MB |
| Export packages, backups | Google Drive | user-owned |

---

## 🆕 Planned Additions (Priority 1)

### Upstash Redis
- **Purpose:** Cache + Session + Rate Limit
- **Free tier:** 10K commands/day
- **Why:** AI response cache (cost save), session store, rate limiting
- **When:** After Priority 0
- **Integration:** API + Worker
- **Status:** [ ] Planned

### Upstash Ratelimit
- **Purpose:** API rate limiting
- **Free tier:** Included with Redis
- **Why:** Protect API from abuse
- **When:** With Redis
- **Status:** [ ] Planned

### PostHog
- **Purpose:** Product Analytics + Feature Flags + A/B
- **Free tier:** 1M events/month
- **Why:** User behavior, feature flags
- **When:** After Priority 0
- **Status:** [ ] Planned

### Doppler / Infisical
- **Purpose:** Secret Management
- **Free tier:** Yes
- **Why:** Centralized env vars, rotation, audit
- **When:** Before Phase 13
- **Status:** [ ] Planned

### Playwright
- **Purpose:** E2E Testing
- **Free tier:** Open source
- **Why:** Priority 0 Step M needs E2E
- **When:** Before Priority 0 Step M
- **Status:** [ ] Planned

### k6 / Artillery
- **Purpose:** Load Testing
- **Free tier:** Open source
- **Why:** Priority 0 Step M needs stress tests
- **When:** Before Priority 0 Step M
- **Status:** [ ] Planned

---

## 🟡 Planned Additions (Priority 2)

### Better Stack Status Page
- **Purpose:** Public status page
- **Free tier:** Yes
- **When:** Before Release (Phase 21)
- **Status:** [ ] Planned

### Mintlify / Docusaurus
- **Purpose:** Docs site
- **Free tier:** Yes
- **When:** After Phase 17
- **Status:** [ ] Planned

### Cloudflare WAF
- **Purpose:** Security
- **Free tier:** Yes (basic)
- **When:** Before Release
- **Status:** [ ] Planned

---

## 🟢 Future Additions (Priority 3 — Card Required)

### Cloudflare R2
- **Purpose:** S3-compatible storage + CDN
- **Free tier:** ⚠️ **Card required**
- **Why:** B2 ထက် CDN ပိုကောင်း, no egress fee
- **When:** Optional (B2 လုံလောက်ရင် မလိုအပ်)
- **Alternative:** B2 + Cloudflare CDN
- **Status:** [ ] Future

### Qdrant / Pinecone
- **Purpose:** Dedicated Vector DB (scale)
- **Free tier:** ⚠️ Limited
- **When:** When pgvector limits reached
- **Status:** [ ] Future

### Meilisearch / Typesense
- **Purpose:** Advanced Search
- **Free tier:** ⚠️ Self-hosted only
- **When:** When Postgres FTS insufficient
- **Status:** [ ] Future

### Inngest / Trigger.dev
- **Purpose:** Workflow Orchestration
- **Free tier:** Yes (limited)
- **When:** When QStash insufficient
- **Status:** [ ] Future

### Cloudflare Stream
- **Purpose:** Video (Vizora Lens future)
- **Free tier:** ⚠️ Paid
- **When:** Vizora video support
- **Status:** [ ] Future

---

## Account Checklist

### Must Have (Now)
- [x] GitHub
- [x] Supabase
- [x] Render
- [x] Netlify
- [x] Cloudflare
- [x] Cloudinary
- [x] Backblaze B2
- [x] Google Cloud (Drive API)
- [x] OpenRouter
- [x] OpenAI
- [x] Sentry
- [x] UptimeRobot
- [x] Umami Cloud
- [x] Axiom
- [x] Brevo
- [x] Upstash (QStash)
- [x] Expo

### Should Have (Priority 1)
- [ ] Upstash Redis
- [ ] PostHog
- [ ] Doppler / Infisical

### Nice to Have (Priority 2)
- [ ] Better Stack
- [ ] Mintlify

### Future (Card Required)
- [ ] Cloudflare R2
- [ ] Qdrant / Pinecone

---

## Install Checklist (Local)

- [x] VS Code
- [x] Git
- [x] Node.js
- [x] Python 3.11+
- [ ] Docker (optional)
- [ ] Ollama (Local AI)
- [ ] Postman (API test)
- [ ] DBeaver (DB GUI)
- [ ] Playwright
- [ ] k6

---

## Service Cost Summary

| Service | Free Tier | Status |
|---|---|---|
| Netlify | 100GB | ✅ |
| Render | 750hr × 2 | ✅ |
| Supabase | 500MB | ⚠️ |
| Upstash Redis | 10K cmd/day | 🆕 |
| Upstash QStash | 500/day | ✅ |
| Cloudinary | 25GB | ✅ |
| Backblaze B2 | 10GB | ⚠️ |
| Google Drive | 15GB | ✅ |
| Cloudflare Workers | 100K/day | ✅ |
| Cloudflare AI Gateway | Free | ✅ |
| Sentry | 5K events | ✅ |
| UptimeRobot | 50 monitors | ✅ |
| Umami Cloud | 100K events | ✅ |
| Axiom | 500GB/month | ✅ |
| Brevo | 300 emails/day | ✅ |
| GitHub Actions | 2000 min | ✅ |
| Expo EAS | Free tier | ✅ |
| **Total** | **$0** | ✅ |

---

## Change Log

| Date | Change |
|---|---|
| 2026-10-06 | Initial file created |
