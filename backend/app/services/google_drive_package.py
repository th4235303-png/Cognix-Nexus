from __future__ import annotations
import json
from typing import Any

def build_file_contents(source: dict[str, Any]) -> dict[str, tuple[str, str]]:
    return {
        "source.json": (json.dumps({"id": source["id"], "url": source["url"], "note": source.get("note"), "created_at": source.get("created_at"), "updated_at": source.get("updated_at")}, ensure_ascii=False, indent=2), "application/json"),
        "original-reference.txt": (source.get("original_text") or "", "text/plain"),
        "summary.md": (source.get("ai_summary") or "", "text/markdown"),
        "myanmar-summary.md": (source.get("approved_myanmar") or source.get("human_edited_myanmar") or source.get("myanmar_translation") or "", "text/markdown"),
        "claims.json": (json.dumps(source.get("claims", []), ensure_ascii=False, indent=2), "application/json"),
        "review.json": (json.dumps({"status": source.get("status"), "critical_warnings": source.get("critical_warnings", []), "source_trust": source.get("source_trust")}, ensure_ascii=False, indent=2), "application/json"),
    }
