from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Store:
    sources: dict[str, dict[str, Any]] = field(default_factory=dict)
    tasks: dict[str, dict[str, Any]] = field(default_factory=dict)
    reviews: dict[str, dict[str, Any]] = field(default_factory=dict)
    exports: dict[str, dict[str, Any]] = field(default_factory=dict)
    activity: list[dict[str, Any]] = field(default_factory=list)
    export_keys: dict[str, str] = field(default_factory=dict)

    def add_activity(self, action: str, target: str, previous: str, new: str) -> None:
        self.activity.insert(0, {
            "id": f"ACT-{uuid4().hex[:8].upper()}",
            "action": action,
            "target": target,
            "previous_state": previous,
            "new_state": new,
            "timestamp": now_iso(),
        })


store = Store()
