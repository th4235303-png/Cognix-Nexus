# Cognix Nexus — AI Agent Behavior

> Preparation and behavior contract; not a production activation switch.

## Safety and evidence
- Agent output is derived evidence, never canonical truth without required review.
- Findings and decisions retain evidence references.
- Cross-owner access fails closed.
- Provider failures fail closed.
- Terminal runs cannot be revived by later lifecycle events.

## Lifecycle
Agent work is intended to move through durable queued/running/review/terminal states with idempotency, lease/heartbeat and fencing controls. Existing durable agent tables are the baseline for future activation.

## Future capabilities
Overnight analysis, cross-book synthesis, contradiction/stale-note detection, progress tracking, morning digest, decision support, writing assistance and Feynman mode are Phase 13 scope.

## Activation rule
Phase 13 runtime orchestration remains disabled until the current release is green, required external gates are evidenced, manual verification is complete, and the phase-specific evidence contract is satisfied.
