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
    brain_books: dict[str, dict[str, Any]] = field(default_factory=dict)
    brain_notes: dict[str, dict[str, Any]] = field(default_factory=dict)
    brain_concepts: dict[str, dict[str, Any]] = field(default_factory=dict)
    brain_concept_links: dict[str, dict[str, Any]] = field(default_factory=dict)
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
        self.brain_books = state.get("brain_books", {})
        self.brain_notes = state.get("brain_notes", {})
        self.brain_concepts = state.get("brain_concepts", {})
        self.brain_concept_links = state.get("brain_concept_links", {})

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

    def create_export_if_absent(self, job: dict[str, Any]) -> dict[str, Any]:
        if self.database:
            saved = self.database.create_export_if_absent(job)
            self.refresh()
            return self.exports[saved['id']]
        self.exports[job['id']] = job
        self.export_keys[job['idempotency_key']] = job['id']
        return job

    def save_brain_book(self, book: dict[str, Any]) -> None:
        if self.database:
            self.database.save_brain_book(book)

    def save_brain_note(self, note: dict[str, Any]) -> None:
        if self.database:
            self.database.save_brain_note(note)

    def save_brain_concept(self, concept: dict[str, Any]) -> None:
        if self.database:
            self.database.save_brain_concept(concept)

    def save_brain_concept_link(self, link: dict[str, Any]) -> None:
        if self.database:
            self.database.save_brain_concept_link(link)

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
