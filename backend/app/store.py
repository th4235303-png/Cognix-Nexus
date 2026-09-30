from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.persistence import Database, configured_database


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
    database: Database | None = None

    def initialize(self) -> None:
        if self.database is None:
            return
        self.database.ensure_schema()
        state = self.database.load_state()
        self.sources = state["sources"]
        self.tasks = state["tasks"]
        self.reviews = state["reviews"]
        self.exports = state["exports"]
        self.activity = state["activity"]
        self.export_keys = state["export_keys"]

    def refresh(self) -> None:
        if self.database is None:
            return
        state = self.database.load_state()
        self.sources = state["sources"]
        self.tasks = state["tasks"]
        self.reviews = state["reviews"]
        self.exports = state["exports"]
        self.activity = state["activity"]
        self.export_keys = state["export_keys"]

    @property
    def persistence_mode(self) -> str:
        return "postgresql" if self.database else "memory-prototype"

    def save_source(self, source: dict[str, Any]) -> None:
        if self.database:
            self.database.save_source(source)

    def save_task(self, task: dict[str, Any]) -> None:
        if self.database:
            self.database.save_task(task)

    def save_review(self, review: dict[str, Any]) -> None:
        if self.database:
            self.database.save_review(review)

    def save_export(self, job: dict[str, Any]) -> None:
        if self.database:
            self.database.save_export(job)

    def add_activity(self, action: str, target: str, previous: str, new: str) -> None:
        event = {
            "id": f"ACT-{uuid4().hex[:8].upper()}",
            "action": action,
            "target": target,
            "previous_state": previous,
            "new_state": new,
            "timestamp": now_iso(),
        }
        self.activity.insert(0, event)
        if self.database:
            self.database.add_activity(event)


store = Store(database=configured_database())
store.initialize()
