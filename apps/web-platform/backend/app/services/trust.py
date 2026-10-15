from __future__ import annotations

from typing import Any

SOURCE_TRUST_WEIGHTS = {
    "official": 1.0,
    "primary": 0.9,
    "reputable": 0.8,
    "expert": 0.75,
    "community": 0.55,
    "unverified": 0.25,
}

CLAIM_CONFIDENCE_WEIGHTS = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4,
    "conflicted": 0.2,
    "unsupported": 0.0,
}


def calculate_trust(source: dict[str, Any]) -> dict[str, Any]:
    source_trust = source.get("source_trust", "unverified")
    claims = source.get("claims", [])
    confidence_values = [
        CLAIM_CONFIDENCE_WEIGHTS.get(claim.get("confidence", "unsupported"), 0.0)
        for claim in claims
    ]
    claim_confidence = (
        "unsupported" if not claims else
        "high" if min(confidence_values) >= 0.85 else
        "medium" if min(confidence_values) >= 0.6 else
        "low" if min(confidence_values) >= 0.3 else
        "conflicted"
    )
    source_score = round(SOURCE_TRUST_WEIGHTS.get(source_trust, 0.25) * 100)
    claim_score = round((sum(confidence_values) / len(confidence_values)) * 100) if confidence_values else 0
    return {
        "source_trust": source_trust,
        "source_trust_score": source_score,
        "claim_confidence": claim_confidence,
        "claim_confidence_score": claim_score,
        "claims_count": len(claims),
    }
