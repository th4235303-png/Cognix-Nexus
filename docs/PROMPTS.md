# Cognix Nexus — Prompt Governance

> Owner: AI/platform
> Last Updated: 2026-10-08

## Rules
- Prompts are versioned implementation inputs, not canonical knowledge.
- Model outputs must preserve source/evidence references where the task requires them.
- System and provider failures must not be hidden by fabricated fallback content.
- Prompt changes require targeted evaluation fixtures before production activation.
- Sensitive/user-owned context must remain inside the applicable owner/privacy boundary.

## Required evaluation dimensions
- citation/source grounding
- hallucination resistance
- structured output validity
- contradiction handling
- partial-evidence behavior
- prompt-injection resistance
- provider failure behavior

## Versioning convention
Use a stable prompt identifier plus semantic revision (for example "feynman.explain@1.0"). Store the revision with evaluation evidence and derived artifacts where reproducibility matters.

## Future prompt families
Active Layer: synthesis, decision support, writing, Feynman.
Learning: path generation, gap analysis, research mode.
Vizora: OCR cleanup, image/diagram analysis and metadata normalization.

No future prompt family is production-activated by this document.
