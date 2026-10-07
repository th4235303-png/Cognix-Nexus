# Cognix Nexus — Agent Contract

## Durable lifecycle
schedule → job → run → finding → human review.

## Safety
- Findings are evidence-bound.
- Findings never become canonical automatically.
- Owner isolation applies to schedules/jobs/runs/findings.
- Lease/fencing semantics prevent stale workers from completing newer work.
- Retry/expiry state is durable.

## Review boundary
Agent output may propose synthesis, decisions, writing, research findings or learning signals. The product must retain source/evidence references and the required human approval boundary.

## Provider boundary
AI providers are configuration-dependent. Missing/invalid provider credentials must produce an explicit failure, not an unverified success state.