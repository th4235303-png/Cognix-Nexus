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
    # These maps support in-memory mode and cache persisted owner IDs after refresh.
    source_owners: dict[str, str] = field(default_factory=dict)
    tasks: dict[str, dict[str, Any]] = field(default_factory=dict)
    reviews: dict[str, dict[str, Any]] = field(default_factory=dict)
    exports: dict[str, dict[str, Any]] = field(default_factory=dict)
    activity: list[dict[str, Any]] = field(default_factory=list)
    export_keys: dict[str, str] = field(default_factory=dict)
    brain_books: dict[str, dict[str, Any]] = field(default_factory=dict)
    brain_book_owners: dict[str, str] = field(default_factory=dict)
    brain_notes: dict[str, dict[str, Any]] = field(default_factory=dict)
    brain_note_owners: dict[str, str] = field(default_factory=dict)
    brain_concepts: dict[str, dict[str, Any]] = field(default_factory=dict)
    brain_concept_owners: dict[str, str] = field(default_factory=dict)
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
        self.source_owners = state.get("source_owners", {})
        self.brain_books = state.get("brain_books", {})
        self.brain_book_owners = state.get("brain_book_owners", {})
        self.brain_notes = state.get("brain_notes", {})
        self.brain_note_owners = state.get("brain_note_owners", {})
        self.brain_concepts = state.get("brain_concepts", {})
        self.brain_concept_owners = state.get("brain_concept_owners", {})
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
        self.source_owners = state.get("source_owners", {})
        self.brain_books = state.get("brain_books", {})
        self.brain_book_owners = state.get("brain_book_owners", {})
        self.brain_notes = state.get("brain_notes", {})
        self.brain_note_owners = state.get("brain_note_owners", {})
        self.brain_concepts = state.get("brain_concepts", {})
        self.brain_concept_owners = state.get("brain_concept_owners", {})
        self.brain_concept_links = state.get("brain_concept_links", {})

    @property
    def persistence_mode(self) -> str:
        return "postgresql" if self.database else "memory-prototype"

    def save_source(self, source: dict[str, Any]) -> None:
        if self.database:
            self.database.save_source(source, self.source_owners.get(source["id"]))

    def set_source_owner(self, source_id: str, owner_id: str | None) -> None:
        if owner_id is not None:
            self.source_owners[source_id] = owner_id

    def get_source_for_owner(self, source_id: str, owner_id: str | None) -> dict[str, Any] | None:
        if self.database:
            return self.database.get_source_for_owner(source_id, owner_id)
        if owner_id is None or self.source_owners.get(source_id) == owner_id:
            return self.sources.get(source_id)
        return None

    def list_sources_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        if self.database:
            return self.database.list_sources_for_owner(owner_id)
        return [
            source for source_id, source in self.sources.items()
            if owner_id is None or self.source_owners.get(source_id) == owner_id
        ]

    def get_task_for_owner(self, task_id: str, owner_id: str | None) -> dict[str, Any] | None:
        if self.database:
            task = self.database.get_task_for_owner(task_id, owner_id)
            if task is None:
                return None
            source = self.database.get_source_for_owner(task["source_id"], owner_id)
            if source is None:
                return None
            self.tasks[task_id] = task
            self.sources[source["id"]] = source
            return task
        task = self.tasks.get(task_id)
        if task is None or self.get_source_for_owner(task["source_id"], owner_id) is None:
            return None
        return task

    def list_tasks_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        if self.database:
            return self.database.list_tasks_for_owner(owner_id)
        return [
            task for task in self.tasks.values()
            if self.get_source_for_owner(task["source_id"], owner_id) is not None
        ]

    def save_task(self, task: dict[str, Any]) -> None:
        if self.database:
            self.database.save_task(task)

    def save_processing_transition(
        self,
        task: dict[str, Any],
        source: dict[str, Any],
        expected_status: str,
        expected_stage: str,
        claim_token: str | None = None,
    ) -> bool:
        if self.database:
            if not self.database.save_processing_transition(
                task,
                source,
                self.source_owners.get(source["id"]),
                expected_status,
                expected_stage,
                claim_token,
            ):
                return False
        self.tasks[task["id"]] = task
        self.sources[source["id"]] = source
        return True

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
            self.database.save_brain_book(book, self.brain_book_owners.get(book["id"]))

    def set_brain_book_owner(self, book_id: str, owner_id: str | None) -> None:
        if owner_id is not None:
            self.brain_book_owners[book_id] = owner_id

    def get_brain_book_for_owner(self, book_id: str, owner_id: str | None) -> dict[str, Any] | None:
        if self.database:
            return self.database.get_book(book_id, owner_id)
        if owner_id is None or self.brain_book_owners.get(book_id) == owner_id:
            return self.brain_books.get(book_id)
        return None

    def list_brain_books_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        if self.database:
            return self.database.list_books(owner_id=owner_id)[0]
        return [
            book for book_id, book in self.brain_books.items()
            if owner_id is None or self.brain_book_owners.get(book_id) == owner_id
        ]

    def list_brain_notes_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        if self.database:
            return self.database.list_brain_notes_for_owner(owner_id)
        return [
            note for note_id, note in self.brain_notes.items()
            if owner_id is None or self.brain_note_owners.get(note_id) == owner_id
        ]

    def get_brain_note_for_owner(self, note_id: str, owner_id: str | None) -> dict[str, Any] | None:
        if self.database:
            return self.database.get_brain_note_for_owner(note_id, owner_id)
        if owner_id is None or self.brain_note_owners.get(note_id) == owner_id:
            return self.brain_notes.get(note_id)
        return None

    def list_note_backlinks_for_owner(
        self,
        note_id: str,
        owner_id: str | None,
    ) -> list[dict[str, Any]] | None:
        if self.database:
            return self.database.list_note_backlinks_for_owner(note_id, owner_id)
        if self.get_brain_note_for_owner(note_id, owner_id) is None:
            return None
        backlinks = []
        for note in self.list_brain_notes_for_owner(owner_id):
            if any(
                source.get("source_type") == "note" and source.get("source_id") == note_id
                for source in note.get("sources", [])
            ):
                backlinks.append(note)
        return backlinks

    def save_brain_note(self, note: dict[str, Any], owner_id: str | None) -> None:
        if owner_id is not None:
            self.brain_note_owners.setdefault(note["id"], owner_id)
        if self.database:
            self.database.save_brain_note(note, owner_id)

    def list_brain_concepts_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        if self.database:
            return self.database.list_brain_concepts_for_owner(owner_id)
        return [
            concept for concept_id, concept in self.brain_concepts.items()
            if owner_id is None or self.brain_concept_owners.get(concept_id) == owner_id
        ]

    def get_brain_concept_for_owner(self, concept_id: str, owner_id: str | None) -> dict[str, Any] | None:
        if self.database:
            return self.database.get_brain_concept_for_owner(concept_id, owner_id)
        if owner_id is None or self.brain_concept_owners.get(concept_id) == owner_id:
            return self.brain_concepts.get(concept_id)
        return None

    def get_brain_concept_by_name_for_owner(
        self,
        name: str,
        owner_id: str | None,
    ) -> dict[str, Any] | None:
        if self.database:
            return self.database.get_brain_concept_by_name_for_owner(name, owner_id)
        normalized_name = name.lower()
        return next(
            (
                concept
                for concept_id, concept in self.brain_concepts.items()
                if (owner_id is None or self.brain_concept_owners.get(concept_id) == owner_id)
                and concept["name"].lower() == normalized_name
            ),
            None,
        )

    def list_concept_links_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        if self.database:
            return self.database.list_concept_links_for_owner(owner_id)
        return [
            link for link in self.brain_concept_links.values()
            if self.get_brain_concept_for_owner(link["from_concept_id"], owner_id) is not None
            and self.get_brain_concept_for_owner(link["to_concept_id"], owner_id) is not None
        ]

    def save_brain_concept(self, concept: dict[str, Any], owner_id: str | None) -> None:
        if owner_id is not None:
            self.brain_concept_owners.setdefault(concept["id"], owner_id)
        if self.database:
            self.database.save_brain_concept(concept, owner_id)

    def save_brain_concept_link(self, link: dict[str, Any], owner_id: str | None) -> None:
        if self.database:
            self.database.save_brain_concept_link(link, owner_id)

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
