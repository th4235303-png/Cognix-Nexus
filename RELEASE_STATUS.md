# Canonical Release Status: Cognix Nexus

> **Current Tracked Repository SHA:** `5bd0ca0449a6a6f61be9c5c0baf0ad603174c8ce`  
> **Target Branch:** `main`  
> **Audit Status:** Conditional Sign-Off (Local Complete, Production Gates Tracked)  
> **Last Verification Date:** 2026-11-10  

---

## Latest production acceptance snapshot — 2026-11-10

**Decision: CONDITIONAL / NOT YET PRODUCTION ACCEPTED.** This snapshot supersedes older timestamps and runtime observations below; historical notes are retained for traceability.

- GitHub Core CI, Production CI/CD, and CodeQL passed on repository revision `e31afbe05faff1b7cd068cbe972169c930a7e0d6`. The production health gate passed API health/readiness, Worker health with PostgreSQL persistence, and frontend HTTPS/HTML. API/Worker exact-revision comparison was skipped because the revision was documentation-only.
- Render API, Worker runtime, and frontend are live, track `main`, and their inspected deployments succeeded. All three are on the Free plan. Do not treat the polling Worker as an always-on queue consumer; paid always-on capacity needs budget approval.
- Supabase `Cognix-Core` is ACTIVE_HEALTHY (PostgreSQL 17, 29 migrations, pgvector 0.8.2, persisted `vector(1536)` embeddings, private `cognix-artifacts` bucket). Key user tables have RLS and owner-scoped policies. Four RLS-enabled public tables have no policies and require product/owner review before changes.
- The connected Supabase restore-drill project is INACTIVE; isolation and restore readiness are unverified. No E2E account exists. No authenticated browser/mobile smoke, production queue job, production corpus acceptance, real provider/storage round trip, Sentry probe, or live restore/rollback was run.
- Cloudflare has no Worker script listed in the connected account; account-level two-factor enforcement is false. Confirm whether Cloudflare Worker routing is in production scope before configuring its secret.
- Recovery drill safety hardening from [PR #112](https://github.com/th4235303-png/Cognix-Nexus/pull/112) is merged at `5bd0ca0449a6a6f61be9c5c0baf0ad603174c8ce`; all PR CI jobs passed on tested head `92e535e2382c8894665a97327eb35e25927cb430`.
- The recovery guardrail PR was merged to `main`; this is a source-code integration and not evidence of live restore acceptance. No production data, secrets, paid plans, auth settings, or Cloudflare account settings were changed. No direct deploy was triggered by these connector actions.

Unconditional production sign-off remains blocked by the operator/device acceptance gates above and the Free Render always-on capacity limitation. See [audit/FINAL_REPORT.md](audit/FINAL_REPORT.md) and [issue #80](https://github.com/th4235303-png/Cognix-Nexus/issues/80) for the detailed evidence and outstanding work.

---

## 1. Release Identification & Contracts
* **Project Name:** Cognix Nexus
* **Assigned Telegram Topic:** `Topic 7 (Supergroup: -1003992125718)`
* **Primary Telegram Bot:** `@CognixNexusBot`
* **Inbound Webhook Target:** `https://cognix-core-ypak.onrender.com/telegram/webhook`
* **Test Suite Status:** Backend Pytest 472 Passed (100% Green), Rate Limit Isolation Added, Mobile PIN Vault Hardened to Per-User Random Salt

---

## 2. Release Gates & Verification Matrix
- [X] Code & Architecture Scan
- [X] Rate Limit Test Fixture isolation in conftest.py
- [X] Mobile PIN PBKDF2 upgraded with per-device random salt & auto-migration
- [ ] Render live service spin-up (resolving 503 on sleeping free tier)
- [ ] Real OAuth browser smoke tests

---

## 3. Policy & Unconditional Production Criteria
This repository must NOT be tagged as `Unconditional Production Ready` until all remaining unchecked gates are signed off with live production evidence.


## Post-snapshot repository integration — 2026-11-10

- Latest main integration: `5bd0ca0449a6a6f61be9c5c0baf0ad603174c8ce` (PR #112 merged).
- PR #112's Core CI, Production CI/CD build/preflight, and CodeQL all passed at tested head `92e535e2382c8894665a97327eb35e25927cb430`. Main-commit status/run lookup returned no additional status entries at time of check.
- The conditional production verdict remains. A safe isolated recovery target, authenticated E2E user, real provider/storage and queue acceptance, and on-device validation still require verification. Free tier is the constraint; do not add paid services.
