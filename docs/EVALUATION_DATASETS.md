# Cognix Nexus — Evaluation Datasets

> Preparation only. These fixtures are not production PASS evidence.
> Last Updated: 2026-10-08

## 1. AI evaluation
Cases cover grounded answers, citation presence, hallucination refusal, structured JSON validity, contradictory evidence and partial evidence.

## 2. Agent evaluation
Cases cover evidence-bound findings, synthesis lineage, owner mismatch, provider failure, retry/idempotency and terminal-event fencing.

## 3. Learning evaluation
Cases cover deterministic decay weighting, interleaving selection, learning-path progression, knowledge-gap coverage and research-mode source lineage.

## 4. Performance benchmarks
Record latency, storage footprint, queue duration, embedding throughput and provider quota consumption with a fixed corpus and environment label.

## 5. Security tests
Cases cover prompt injection, RLS ownership isolation, SSRF validation/redirects, secret non-disclosure and provider failure fail-closed behavior.

## Fixture rules
- Small and deterministic.
- No real secrets or personal data.
- Owner IDs are synthetic.
- Evidence references are explicit.
- Expected outcomes are machine-checkable.
- Runtime activation and release evidence remain separate.
