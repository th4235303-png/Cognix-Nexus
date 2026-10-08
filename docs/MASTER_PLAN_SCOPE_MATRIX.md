# Cognix Nexus — Master Plan v4 Scope Matrix

> This is a scope reconciliation/control document. It does not mark features complete.
> Last Updated: 2026-10-08

## Status meanings
- **Existing**: already implemented or documented elsewhere; do not duplicate.
- **Foundation**: contract/tests/design prepared; runtime feature is not activated.
- **Planned**: explicitly tracked for future implementation.
- **External gate**: requires real provider/device/account/manual evidence.

| Scope | Phase | Current classification |
|---|---:|---|
| Document types classifier | 17 | Planned |
| OCR review + low-confidence highlight | 17 | Planned |
| Medical/legal disclaimer | 17 | Planned |
| Document lifecycle states | 17 | Planned |
| MM↔JP/KR tutor | 17 | Planned |
| Parallel text / grammar | 17 | Planned |
| Furigana/romaji + pronunciation | 17 | Planned |
| TTS / writing correction / role-play | 17 | Planned |
| Tutor quizzes + CEFR/JLPT/TOPIK | 17 | Planned |
| TOTP | 16 | Planned |
| SSH key storage | 16 | Planned |
| k-anonymity breach check | 16 | Planned |
| Emergency kit | 16 | Planned |
| Encrypted Vault export/import | 16 | Planned |
| Agent mode | 13 | Foundation + planned runtime |
| Synthesis engine | 13 | Foundation + planned runtime |
| Decision support | 13 | Foundation + planned runtime |
| Writing assistant | 13 | Foundation + planned runtime |
| Feynman mode | 13 | Foundation + planned runtime |
| Decay / interleaving / learning paths | 14 | Foundation + planned runtime |
| Knowledge gaps / research mode | 14 | Foundation + planned runtime |
| Personal timeline | 15 | Foundation + planned runtime |
| Local-only mood mode | 15 | Foundation + planned runtime |
| User-triggered ambient learning | 15 | Foundation + planned runtime |
| Context restoration | 15 | Foundation + planned runtime |
| Time capsule | 15 | Foundation + planned runtime |
| Personal wiki | 16 | Foundation + planned runtime |
| Growth visualization | 16 | Foundation + planned runtime |
| Idea generator | 16 | Foundation + planned runtime |
| Offline-first AI boundary | 16 | Foundation + planned runtime |
| Legacy mode | 16 | Foundation + planned runtime |
| Batch media upload | 18 | Planned |
| OCR/vision diagram/chart analysis | 18 | Foundation + planned runtime |
| Metadata extraction | 18 | Planned |
| Media review + links | 18 | Foundation + planned runtime |
| Drive media package | 18 | Planned |
| Offline reader | 19 | Planned |
| Share-sheet/capture | 19 | Planned |
| Camera OCR | 19 | Foundation + planned runtime |
| Voice capture | 19 | Foundation + planned runtime |
| Push notifications | 19 | Foundation + planned runtime |
| Biometric Vault unlock | 19 | Foundation + planned runtime |
| Native JP/KR UI | 19 | Planned |
| WCAG AA/responsive polish | 19 | External gate + planned polish |
| AI/Agent/Learning/Performance/Security evaluations | 20 | Seed fixtures prepared |
| Architecture/Data/Pipeline/Prompts/Troubleshooting/Changelog/User Guide/Agent docs | P0/P1 | Canonical coverage tracked |
| PostHog | Backlog | Optional |
| Better Stack | Backlog | Optional |
| Mintlify/Docusaurus | Backlog | Optional |

## Release guard

No row in this matrix overrides the release sequence:

**CI PASS → provider/storage/Book acceptance → authenticated browser → recovery/GDPR/observability/accessibility/performance/mobile → grouped manual verification → final production smoke → release approval → Phase 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21.**

Future foundation work can continue in parallel. Production runtime activation cannot.
