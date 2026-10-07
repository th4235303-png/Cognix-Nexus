# Cognix Nexus — Working Tool & Documentation Protocol

> Owner: Engineering workflow
> Update when: repository workflow, tool matrix, phase protocol, or documentation rules change
> Last Updated: 2026-10-08
> Do NOT put here: product roadmap details, live production evidence, secrets, or domain architecture.

## 1. Read order
1. README.md
2. PROJECT_OVERVIEW.md
3. CURRENT_STATE.md
4. ROADMAP.md
5. UI_DESIGN_SYSTEM.md for frontend work
6. SECURITY.md
7. relevant docs/*
8. current code/config/evidence before changing status

## 2. Git workflow
ADR-007: Cognix implementation and documentation changes land on main.
Operating sequence: verify → implement/fix → test → production verify → update evidence → main.
Never commit secrets. Do not convert code-configured state into VERIFIED without real evidence.

## 3. Phase completion protocol
1. Identify scope and acceptance criteria.
2. Read canonical owner documents.
3. Inspect actual code/config and evidence.
4. Implement/fix within phase boundary.
5. Run relevant checks.
6. Capture concrete evidence.
7. Update canonical documentation.
8. Self-check ownership, links, status labels and remaining gates.

## 4. Documentation Update Protocol
### Trigger table
| Change | Canonical owner |
|---|---|
| Project identity/short snapshot | README |
| Architecture/product model | PROJECT_OVERVIEW |
| Current status/evidence/gates | CURRENT_STATE |
| Strategic phases and acceptance | ROADMAP |
| UI rules/tokens/components/a11y | UI_DESIGN_SYSTEM |
| Working/read/update protocol | TOOL |
| Security/threat model | SECURITY |
| Domain implementation detail | docs/* |
| Feature behavior | docs/features/* |
| Operational procedure | docs/runbooks/* |
| Historical material | archive/legacy/* |

### Session start
Read canonical files, confirm branch/scope, and treat unresolved facts as VERIFY.

### Session end
Update status only from evidence; record blockers/deferred work; keep decisions traceable; check links/ownership; confirm no knowledge became orphaned.

### Doc drift rule
If a document claims current state, it must point to canonical status/evidence. A historical source must not remain an active source of truth.

## 5. Tools matrix
| Tool/service | Role | Status source |
|---|---|---|
| GitHub + Actions | source/CI | CURRENT_STATE/evidence |
| Render | API/worker | CURRENT_STATE + deployment docs |
| Netlify | frontend | CURRENT_STATE + deployment docs |
| Supabase | DB/Auth/Storage | CURRENT_STATE + database/storage docs |
| Cloudinary | media | CURRENT_STATE + storage docs |
| Backblaze B2 | large originals | CURRENT_STATE + storage docs |
| Google Drive | export/backup | CURRENT_STATE + deployment/storage docs |
| OpenAI-compatible provider | AI | CURRENT_STATE + AI/RAG docs |
| Sentry | monitoring | CURRENT_STATE |
| Expo/EAS | mobile | CURRENT_STATE |
| Optional backlog | Upstash/PostHog/Doppler/k6/Better Stack/Mintlify/Cloudflare WAF/R2/vector/search/orchestration | ROADMAP |

## 6. Definition of done
- Correct canonical owner exists.
- Code/config matches documented intent.
- Relevant tests pass.
- External verification is performed where required.
- Evidence is captured before status promotion.
- No secrets are committed.
- No duplicate source-of-truth document is created.
- All changes land on main.

## 7. Evidence rules
Status labels: DONE / VERIFIED / PENDING / BLOCKED / DEFERRED / NEXT / VERIFY.
Always distinguish repository migration head vs live head; code-configured vs externally verified; implemented vs production-tested; account availability vs provider verification.
