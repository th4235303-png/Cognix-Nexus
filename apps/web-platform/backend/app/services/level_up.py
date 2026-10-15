from __future__ import annotations
from datetime import datetime, timedelta, timezone
from itertools import cycle, islice
import re

def feynman_grade(explanation: str, required_terms: list[str] | None = None) -> dict:
    text = explanation.strip()
    words = re.findall(r"\b\w+\b", text)
    terms = [t.lower() for t in (required_terms or [])]
    hits = sum(1 for t in terms if t in text.lower())
    clarity = min(100, len(words) * 10)
    coverage = 100 if not terms else round(hits / len(terms) * 100)
    score = round((clarity + coverage) / 2)
    gaps = [t for t in terms if t not in text.lower()]
    return {"score": score, "gaps": gaps, "mastered": score >= 90 and not gaps}

def decay_review(stability: float, difficulty: float, last_reviewed: datetime, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    elapsed = max(0.0, (now - last_reviewed).total_seconds() / 86400)
    stability = max(0.1, stability)
    retention = 2 ** (-elapsed / stability)
    risk = round(1 - retention, 4)
    interval = max(1, round(stability * max(0.25, 1.0 - difficulty / 20)))
    return {"elapsed_days": round(elapsed, 3), "retention": round(retention, 4), "decay_risk": risk, "recommended_interval_days": interval}

def interleave(subjects: list[str], rounds: int = 3) -> list[str]:
    unique = list(dict.fromkeys(s for s in subjects if s.strip()))
    if len(unique) < 2:
        raise ValueError("Interleaving requires at least two subjects")
    return list(islice(cycle(unique), len(unique) * max(1, rounds)))

def build_learning_path(items: list[dict], goal: str) -> dict:
    allowed = [i for i in items if i.get("source_type") in {"book", "note", "concept", "source"}]
    allowed.sort(key=lambda x: (x.get("priority", 0), x.get("title", "")), reverse=True)
    return {"goal": goal, "library_only": True, "items": allowed[:20], "count": min(20, len(allowed))}

def analyze_gap(subject: str, known: list[str], required: list[str]) -> dict:
    known_set = {x.strip().lower() for x in known}
    gaps = [x for x in required if x.strip().lower() not in known_set]
    return {"subject": subject, "known": len(known_set), "required": len(required), "gaps": gaps, "status": "open" if gaps else "covered"}

def synthesis_contract(question: str, source_ids: list[str], findings: list[dict]) -> dict:
    ids = list(dict.fromkeys(source_ids))
    if len(ids) < 3:
        raise ValueError("Synthesis requires at least three distinct sources")
    cited = [f for f in findings if f.get("source_id") in ids]
    return {"question": question, "source_ids": ids, "findings": cited, "source_count": len(ids), "evidence_complete": len(cited) >= 1}

def decision_balance(options: list[dict], evidence: list[dict]) -> dict:
    counts = {str(o.get("id") or o.get("title") or i): 0 for i, o in enumerate(options)}
    for item in evidence:
        oid = str(item.get("option_id", ""))
        if oid in counts:
            counts[oid] += 1
    return {"options": counts, "evidence_count": len(evidence), "needs_more_evidence": any(v == 0 for v in counts.values())}

def writing_citation_check(source_ids: list[str], cited_ids: list[str]) -> dict:
    allowed = set(source_ids)
    cited = set(cited_ids)
    missing = sorted(cited - allowed)
    return {"valid": not missing and bool(cited), "missing_source_ids": missing, "citation_count": len(cited)}

def research_mode(source_ids: list[str], claims: list[dict]) -> dict:
    allowed = set(source_ids)
    bound = [c for c in claims if c.get("source_id") in allowed]
    return {"source_ids": list(allowed), "claims": bound, "requires_review": True, "auto_approve": False}

def restore_context(events: list[dict], max_items: int = 20) -> dict:
    ordered = sorted(events, key=lambda x: str(x.get("at") or x.get("occurred_at") or ""), reverse=True)
    return {"items": ordered[:max_items], "restored_at": datetime.now(timezone.utc).isoformat()}

def compounding_score(concepts: int, notes: int, links: int, sources: int) -> float:
    if max(concepts, notes, links, sources) <= 0:
        return 0.0
    return round((concepts * 1.5 + notes + links * 2 + sources * 0.5), 2)

def wiki_projection(title: str, body: str, source_ids: list[str]) -> dict:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "untitled"
    return {"title": title, "slug": slug, "body": body, "source_ids": list(dict.fromkeys(source_ids)), "visibility": "private"}

def detect_sync_conflict(base_revision: int, local_revision: int, remote_revision: int, local: dict, remote: dict) -> dict:
    conflict = local_revision != base_revision and remote_revision != base_revision and local != remote
    return {"conflict": conflict, "status": "needs_review" if conflict else "mergeable", "base_revision": base_revision}

def legacy_policy() -> dict:
    return {"encrypted": True, "server_plaintext": False, "beneficiary_required_for_release": True, "auto_release": False}
