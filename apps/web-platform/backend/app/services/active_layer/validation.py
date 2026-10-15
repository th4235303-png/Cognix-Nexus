from __future__ import annotations

"""Fail-closed validation for Phase 13 evidence-bound contracts."""

from .contracts import DecisionRecord, Finding


def finding_ready_for_review(finding: Finding) -> bool:
    return bool(finding.statement.strip() and finding.evidence and finding.review_state != "draft")


def decision_has_evidence(decision: DecisionRecord) -> bool:
    return bool(decision.decision.strip() and decision.rationale.strip() and decision.evidence)
