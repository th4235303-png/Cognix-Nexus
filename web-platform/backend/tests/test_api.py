import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.store import store
from app.worker import run_once
from app.services.research_processor import ProcessingResult
from app.services.processing import TaskLeaseLost, advance
from app.services.task_retry import retry_delay_seconds, retry_ready
from app.routers.brain_advanced import _schedule


class MemoryOwnershipDatabase:
    def __init__(self):
        self.sources = {}
        self.source_owners = {}
        self.books = {}
        self.book_owners = {}
        self.tasks = {}
        self.reviews = {}
        self.exports = {}
        self.export_keys = {}
        self.brain_notes = {}
        self.brain_note_owners = {}
        self.brain_concepts = {}
        self.brain_concept_owners = {}
        self.brain_concept_links = {}
        self.language_cards = {}

    def load_state(self):
        return {
            "sources": dict(self.sources),
            "source_owners": dict(self.source_owners),
            "tasks": dict(self.tasks),
            "reviews": dict(self.reviews),
            "exports": dict(self.exports),
            "export_keys": dict(self.export_keys),
            "activity": [],
            "brain_books": dict(self.books),
            "brain_book_owners": dict(self.book_owners),
            "brain_notes": dict(self.brain_notes),
            "brain_note_owners": dict(self.brain_note_owners),
            "brain_concepts": dict(self.brain_concepts),
            "brain_concept_owners": dict(self.brain_concept_owners),
            "brain_concept_links": dict(self.brain_concept_links),
        }

    def save_source(self, source, owner_id=None):
        self.sources[source["id"]] = source
        self.source_owners.setdefault(source["id"], owner_id)

    def get_source_for_owner(self, source_id, owner_id):
        if source_id not in self.sources:
            return None
        if owner_id is not None and self.source_owners.get(source_id) != owner_id:
            return None
        return self.sources[source_id]

    def list_sources_for_owner(self, owner_id):
        return [
            source for source_id, source in self.sources.items()
            if owner_id is None or self.source_owners.get(source_id) == owner_id
        ]

    def save_task(self, task):
        self.tasks[task["id"]] = task

    def save_processing_transition(
        self, task, source, expected_status, expected_stage, claim_token=None
    ):
        self.tasks[task["id"]] = task
        self.sources[source["id"]] = source
        return True

    def get_task_for_owner(self, task_id, owner_id):
        task = self.tasks.get(task_id)
        if task is None or self.get_source_for_owner(task["source_id"], owner_id) is None:
            return None
        return task

    def list_tasks_for_owner(self, owner_id):
        return [
            task for task in self.tasks.values()
            if self.get_source_for_owner(task["source_id"], owner_id) is not None
        ]

    def save_brain_book(self, book, owner_id=None):
        self.books[book["id"]] = book
        self.book_owners.setdefault(book["id"], owner_id)

    def get_book(self, book_id, owner_id=None):
        if owner_id is not None and self.book_owners.get(book_id) != owner_id:
            return None
        return self.books.get(book_id)

    def list_books(self, limit=50, offset=0, owner_id=None):
        books = [
            book for book_id, book in self.books.items()
            if owner_id is None or self.book_owners.get(book_id) == owner_id
        ]
        return books[offset:offset + limit], len(books)

    def search_book(self, book_id, query, limit=20, owner_id=None):
        book = self.get_book(book_id, owner_id)
        if book is None:
            return [], 0
        matches = []
        for chapter in book["chapters"]:
            for chunk in chapter["chunks"]:
                if query.lower() in chunk["content"].lower():
                    matches.append({
                        "chunk_id": chunk["id"],
                        "chapter_id": chapter["id"],
                        "chapter_title": chapter["title"],
                        "sequence": chunk["sequence"],
                        "score": 1,
                        "content": chunk["content"],
                    })
        return matches[:limit], len(matches)

    def get_book_by_content_hash(self, content_hash, owner_id):
        return next(
            (
                book for book_id, book in self.books.items()
                if book.get("content_hash") == content_hash
                and (owner_id is None or self.book_owners.get(book_id) == owner_id)
            ),
            None,
        )

    def save_review(self, review):
        self.reviews[review["source_id"]] = review

    def add_activity(self, event):
        pass

    def list_brain_notes_for_owner(self, owner_id):
        return [
            note for note_id, note in self.brain_notes.items()
            if owner_id is None or self.brain_note_owners.get(note_id) == owner_id
        ]

    def get_brain_note_for_owner(self, note_id, owner_id):
        if owner_id is not None and self.brain_note_owners.get(note_id) != owner_id:
            return None
        return self.brain_notes.get(note_id)

    def list_note_backlinks_for_owner(self, note_id, owner_id):
        if self.get_brain_note_for_owner(note_id, owner_id) is None:
            return None
        return [
            note for note in self.list_brain_notes_for_owner(owner_id)
            if any(
                source.get("source_type") == "note" and source.get("source_id") == note_id
                for source in note.get("sources", [])
            )
        ]

    def save_brain_note(self, note, owner_id):
        self.brain_notes[note["id"]] = note
        if owner_id is not None:
            self.brain_note_owners.setdefault(note["id"], owner_id)
        note["sources"] = (
            [{"source_type": note["source_type"], "source_id": note["source_id"]}]
            if note.get("source_type") and note.get("source_id") else []
        )

    def list_brain_concepts_for_owner(self, owner_id):
        return [
            concept for concept_id, concept in self.brain_concepts.items()
            if owner_id is None or self.brain_concept_owners.get(concept_id) == owner_id
        ]

    def get_brain_concept_for_owner(self, concept_id, owner_id):
        if owner_id is not None and self.brain_concept_owners.get(concept_id) != owner_id:
            return None
        return self.brain_concepts.get(concept_id)

    def get_brain_concept_by_name_for_owner(self, name, owner_id):
        normalized_name = name.lower()
        return next(
            (
                concept for concept_id, concept in self.brain_concepts.items()
                if (owner_id is None or self.brain_concept_owners.get(concept_id) == owner_id)
                and concept["name"].lower() == normalized_name
            ),
            None,
        )

    def list_concept_links_for_owner(self, owner_id):
        return [
            link for link in self.brain_concept_links.values()
            if self.get_brain_concept_for_owner(link["from_concept_id"], owner_id) is not None
            and self.get_brain_concept_for_owner(link["to_concept_id"], owner_id) is not None
        ]

    def save_brain_concept(self, concept, owner_id):
        self.brain_concepts[concept["id"]] = concept
        if owner_id is not None:
            self.brain_concept_owners.setdefault(concept["id"], owner_id)

    def save_brain_concept_link(self, link, owner_id):
        if (
            self.get_brain_concept_for_owner(link["from_concept_id"], owner_id) is None
            or self.get_brain_concept_for_owner(link["to_concept_id"], owner_id) is None
        ):
            raise RuntimeError("Concept link ownership mismatch")
        self.brain_concept_links[link["id"]] = link

    def create_language_card(self, card, owner_id):
        row = {
            **card,
            "owner_id": owner_id,
            "due_at": "2000-01-01T00:00:00+00:00",
            "stability": 0,
            "difficulty": 5,
            "reps": 0,
            "lapses": 0,
            "state": "learning",
        }
        self.language_cards[card["id"]] = row
        return row

    def list_language_cards_due_for_owner(self, owner_id, limit):
        return [
            card for card in self.language_cards.values()
            if owner_id is None or card["owner_id"] == owner_id
        ][:limit]

    def review_language_card(self, card_id, owner_id, rating, schedule):
        card = self.language_cards.get(card_id)
        if card is None or (owner_id is not None and card["owner_id"] != owner_id):
            return None
        stability, difficulty, reps, lapses, state, due = schedule(card, rating)
        card.update({
            "stability": stability,
            "difficulty": difficulty,
            "reps": reps,
            "lapses": lapses,
            "state": state,
            "due_at": due.isoformat(),
        })
        return card


class CognixApiTests(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict("os.environ", {"COGNIX_DEV_MODE": "true"}, clear=False)
        self.env_patch.start()
        self.processing_patch = patch(
            "app.services.processing.process_stage",
            side_effect=lambda stage, source: ProcessingResult(
                original_text="Test source text" if stage == "extracting" else None,
                cleaned_text="Test source text" if stage == "cleaning" else None,
                summary="Test summary" if stage == "summarizing" else None,
                translation="Test Myanmar translation" if stage == "translating" else None,
                key_points=["Test key point"] if stage == "key_points" else None,
            ),
        )
        self.processing_patch.start()
        store.sources.clear()
        store.source_owners.clear()
        store.tasks.clear()
        store.reviews.clear()
        store.exports.clear()
        store.activity.clear()
        store.export_keys.clear()
        store.brain_books.clear()
        store.brain_book_owners.clear()
        store.brain_notes.clear()
        store.brain_note_owners.clear()
        store.brain_concepts.clear()
        store.brain_concept_owners.clear()
        store.brain_concept_links.clear()
        self.client = TestClient(app)

    def test_health_and_root_metadata(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        root = self.client.get("/")
        self.assertEqual(root.status_code, 200)
        self.assertEqual(root.json()["service"], "cognix-nexus-api")
        self.assertIn("x-request-id", health.headers)
        ready = self.client.get("/ready")
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json()["persistence_mode"], "memory-prototype")

    def test_duplicate_and_processing(self):
        first = self.client.post("/sources", json={"url": "https://example.com/research"})
        self.assertEqual(first.status_code, 201)
        source = first.json()["source"]

        duplicate = self.client.post(
            "/sources", json={"url": "https://example.com/research/"}
        )
        self.assertEqual(duplicate.status_code, 201)
        self.assertEqual(duplicate.json()["status"], "duplicate_ignored")

        task = self.client.post("/processing", json={"source_id": source["id"]})
        self.assertEqual(task.status_code, 202)
        task_id = task.json()["id"]
        duplicate_task = self.client.post("/processing", json={"source_id": source["id"]})
        self.assertEqual(duplicate_task.json()["id"], task_id)

        advanced = self.client.post(f"/processing/{task_id}/advance")
        self.assertEqual(advanced.status_code, 200)
        self.assertEqual(advanced.json()["stage"], "extracting")
        self.assertEqual(advanced.json()["progress"], 11)

        retried = self.client.post(f"/processing/{task_id}/retry")
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(retried.json()["retry_count"], 1)
        self.assertEqual(retried.json()["stage"], "queued")

    def test_processing_retries_are_bounded(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/retry-limit"}
        ).json()["source"]
        task = self.client.post("/processing", json={"source_id": source["id"]}).json()
        task_id = task["id"]

        for expected_retry_count in range(1, 6):
            store.tasks[task_id]["status"] = "failed"
            retry = self.client.post(f"/processing/{task_id}/retry")
            self.assertEqual(retry.status_code, 200)
            self.assertEqual(retry.json()["retry_count"], expected_retry_count)

        store.tasks[task_id]["status"] = "failed"
        rejected = self.client.post(f"/processing/{task_id}/retry")
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(rejected.json()["detail"]["code"], "RETRY_LIMIT_REACHED")

    def test_retry_backoff_is_exponential_and_bounded(self):
        self.assertEqual(
            [retry_delay_seconds(count) for count in range(7)],
            [0, 5, 10, 20, 40, 80, 160],
        )
        self.assertEqual(retry_delay_seconds(20), 300)

    def test_retry_backoff_uses_injected_time_and_only_delays_queued_retries(self):
        task = {
            "status": "queued",
            "retry_count": 2,
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertFalse(retry_ready(task, start.replace(second=9)))
        self.assertTrue(retry_ready(task, start.replace(second=10)))
        self.assertTrue(retry_ready({**task, "status": "running"}, start))

    def test_lost_lease_does_not_persist_processing_results(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/lost-lease"}
        ).json()["source"]
        task = self.client.post("/processing", json={"source_id": source["id"]}).json()

        with self.assertRaises(TaskLeaseLost):
            advance(task["id"], claim_token="stale-token", lease_is_valid=lambda: False)

        self.assertEqual(store.tasks[task["id"]]["stage"], "queued")
        self.assertEqual(store.sources[source["id"]]["processing_stage"], "queued")
        self.assertIsNone(store.sources[source["id"]]["original_text"])

    def test_completed_task_cannot_be_advanced_retried_or_reclaimed(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/completed-task"}
        ).json()["source"]
        task = self.client.post("/processing", json={"source_id": source["id"]}).json()
        store.tasks[task["id"]].update({"status": "completed", "stage": "needs_review"})

        self.assertEqual(self.client.post(f"/processing/{task['id']}/advance").status_code, 409)
        self.assertEqual(self.client.post(f"/processing/{task['id']}/retry").status_code, 409)
        self.assertEqual(run_once(), 0)
        self.assertEqual(store.tasks[task["id"]]["stage"], "needs_review")

    def test_approved_only_export_and_idempotency(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/approved"}
        ).json()["source"]

        blocked = self.client.post(
            "/exports/google-drive",
            json={"source_id": source["id"], "idempotency_key": "key-1"},
        )
        self.assertEqual(blocked.status_code, 409)

        self.client.patch(f"/sources/{source['id']}/translation", json={"human_edited_myanmar": "Approved test translation"})
        self.client.post(f"/reviews/{source['id']}/approve", json={})
        exported = self.client.post(
            "/exports/google-drive",
            json={"source_id": source["id"], "idempotency_key": "key-1"},
        )
        replay = self.client.post(
            "/exports/google-drive",
            json={"source_id": source["id"], "idempotency_key": "key-1"},
        )
        self.assertEqual(exported.status_code, 202)
        self.assertEqual(replay.json()["id"], exported.json()["id"])
        advanced = self.client.post(f"/exports/{exported.json()['id']}/advance")
        self.assertEqual(advanced.status_code, 200)
        self.assertEqual(advanced.json()["status"], "uploading")
        completed = self.client.post(f"/exports/{exported.json()['id']}/advance")
        self.assertEqual(completed.json()["status"], "exported")
        self.assertTrue(completed.json()["drive_reference"].startswith("mock-drive://"))

    def test_critical_warning_blocks_approval(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/warning"}
        ).json()["source"]
        store.sources[source["id"]]["critical_warnings"] = ["Missing citation"]

        blocked = self.client.post(f"/reviews/{source['id']}/approve", json={})
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["detail"]["code"], "CRITICAL_WARNINGS")
        self.assertEqual(store.sources[source["id"]]["status"], "new")

    def test_approval_requires_translation(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/missing-translation"}
        ).json()["source"]
        store.sources[source["id"]].update(
            {"status": "needs_review", "processing_stage": "needs_review"}
        )

        blocked = self.client.post(f"/reviews/{source['id']}/approve", json={})

        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["detail"]["code"], "MISSING_TRANSLATION")
        self.assertEqual(store.sources[source["id"]]["status"], "needs_review")
        self.assertNotIn(source["id"], store.reviews)

    def _create_task_at_review(self, critical_warnings=None, translation="Reviewed translation"):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/review-gate"}
        ).json()["source"]
        task = self.client.post(
            "/processing", json={"source_id": source["id"]}
        ).json()
        store.sources[source["id"]].update(
            {
                "status": "needs_review",
                "processing_stage": "needs_review",
                "critical_warnings": critical_warnings or [],
                "myanmar_translation": translation,
            }
        )
        store.tasks[task["id"]].update(
            {"stage": "needs_review", "status": "completed", "progress": 89}
        )
        return source["id"], task["id"]

    def test_processing_advance_cannot_approve_task_at_review(self):
        source_id, task_id = self._create_task_at_review()

        response = self.client.post(f"/processing/{task_id}/advance")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "REVIEW_REQUIRED")
        self.assertEqual(store.tasks[task_id]["stage"], "needs_review")
        self.assertEqual(store.sources[source_id]["status"], "needs_review")
        self.assertNotIn(source_id, store.reviews)

    def test_processing_advance_cannot_bypass_critical_review_warnings(self):
        source_id, task_id = self._create_task_at_review(
            critical_warnings=["Missing citation"]
        )

        response = self.client.post(f"/processing/{task_id}/advance")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(store.tasks[task_id]["stage"], "needs_review")
        self.assertEqual(store.sources[source_id]["status"], "needs_review")
        self.assertNotIn(source_id, store.reviews)

    def test_processing_advance_cannot_bypass_missing_translation(self):
        source_id, task_id = self._create_task_at_review(translation=None)

        response = self.client.post(f"/processing/{task_id}/advance")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(store.tasks[task_id]["stage"], "needs_review")
        self.assertEqual(store.sources[source_id]["status"], "needs_review")
        self.assertNotIn(source_id, store.reviews)

    def test_review_endpoint_approves_task_at_review(self):
        source_id, task_id = self._create_task_at_review()

        response = self.client.post(f"/reviews/{source_id}/approve", json={})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "approved")
        self.assertEqual(store.tasks[task_id]["stage"], "needs_review")
        self.assertEqual(store.sources[source_id]["status"], "approved")
        self.assertEqual(
            store.sources[source_id]["approved_myanmar"], "Reviewed translation"
        )
        self.assertEqual(store.reviews[source_id]["status"], "approved")
        self.assertTrue(
            any(
                event["action"] == "approved" and event["target"] == source_id
                for event in store.activity
            )
        )

    def test_claims_and_trust_score_are_separate(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/claims"}
        ).json()["source"]
        claim = self.client.post(
            f"/sources/{source['id']}/claims",
            json={
                "text": "A claim needing review",
                "excerpt": "Supporting excerpt",
                "location": "Section 2",
                "confidence": "low",
                "verification_state": "unsupported",
            },
        )
        self.assertEqual(claim.status_code, 201)
        score = self.client.get(f"/sources/{source['id']}/trust-score")
        self.assertEqual(score.status_code, 200)
        self.assertEqual(score.json()["source_trust"], "unverified")
        self.assertEqual(score.json()["claim_confidence"], "low")
        self.assertGreaterEqual(len(store.sources[source["id"]]["critical_warnings"]), 1)

        updated = self.client.patch(
            f"/sources/{source['id']}/trust",
            json={"source_trust": "official"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["source_trust"], "official")
        self.assertEqual(updated.json()["claim_confidence"], "low")

    def test_processing_retry_resets_source_state(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/retry-state"}
        ).json()["source"]
        task = self.client.post("/processing", json={"source_id": source["id"]}).json()
        self.client.post(f"/processing/{task['id']}/advance")
        retried = self.client.post(f"/processing/{task['id']}/retry")
        self.assertEqual(retried.status_code, 200)
        refreshed = self.client.get(f"/sources/{source['id']}")
        self.assertEqual(refreshed.json()["status"], "processing")
        self.assertEqual(refreshed.json()["processing_stage"], "queued")

    def test_export_retry_requeues_retryable_job(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/export-retry"}
        ).json()["source"]
        self.client.patch(f"/sources/{source['id']}/translation", json={"human_edited_myanmar": "Approved test translation"})
        self.client.post(f"/reviews/{source['id']}/approve", json={})
        exported = self.client.post(
            "/exports/google-drive",
            json={"source_id": source["id"], "idempotency_key": "retry-key"},
        ).json()
        store.exports[exported["id"]]["status"] = "retry_pending"
        retried = self.client.post(f"/exports/{exported['id']}/retry")
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(retried.json()["status"], "queued")

    def test_translation_edit_persists(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/translation"}
        ).json()["source"]
        response = self.client.patch(
            f"/sources/{source['id']}/translation",
            json={"human_edited_myanmar": "လူက ပြင်ဆင်ထားသော ဘာသာပြန်"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["human_edited_myanmar"], "လူက ပြင်ဆင်ထားသော ဘာသာပြန်")
        fetched = self.client.get(f"/sources/{source['id']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["human_edited_myanmar"], "လူက ပြင်ဆင်ထားသော ဘာသာပြန်")

    def test_activity_records_state_changes(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/activity"}
        ).json()["source"]
        task = self.client.post(
            "/processing", json={"source_id": source["id"]}
        ).json()
        self.client.post(f"/processing/{task['id']}/advance")

        activity = self.client.get("/activity")
        self.assertEqual(activity.status_code, 200)
        self.assertGreaterEqual(activity.json()["total"], 3)


    def tearDown(self):
        self.processing_patch.stop()
        self.env_patch.stop()

    def test_brain_vault_book_note_concept_and_query(self):
        book = self.client.post(
            "/brain/books",
            json={
                "title": "Test Brain Book",
                "author": "Cognix",
                "language": "en",
                "file_type": "text",
                "text": "Habit formation depends on repetition.\n\nSpaced repetition improves recall.",
            },
        )
        self.assertEqual(book.status_code, 201)
        book_id = book.json()["id"]
        self.assertGreaterEqual(book.json()["chunk_count"], 1)

        fetched = self.client.get(f"/brain/books/{book_id}")
        self.assertEqual(fetched.status_code, 200)
        self.assertTrue(fetched.json()["chapters"][0]["chunks"][0]["content"].startswith("Habit formation depends on repetition."))

        search = self.client.get(f"/brain/books/{book_id}/search", params={"q": "repetition"})
        self.assertEqual(search.status_code, 200)
        self.assertGreaterEqual(search.json()["total"], 1)

        note = self.client.post(
            "/brain/notes",
            json={"title": "Habit Note", "content": "Repetition strengthens recall.", "source_type": "book", "source_id": book_id},
        )
        self.assertEqual(note.status_code, 201)

        concept = self.client.post(
            "/brain/concepts",
            json={"name": "Spaced Repetition", "description": "A learning method."},
        )
        self.assertEqual(concept.status_code, 201)
        duplicate = self.client.post("/brain/concepts", json={"name": "spaced repetition"})
        self.assertEqual(duplicate.status_code, 201)
        self.assertEqual(duplicate.json()["id"], concept.json()["id"])

        query = self.client.get("/brain/query", params={"q": "recall"})
        self.assertEqual(query.status_code, 200)
        self.assertGreaterEqual(query.json()["total"], 1)
        self.assertEqual(query.json()["mode"], "evidence_search")



    def test_security_headers_and_request_id_are_consistent(self):
        response = self.client.get("/health", headers={"x-request-id": "test-request-123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-request-id"], "test-request-123")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "strict-origin-when-cross-origin")
        self.assertIn("geolocation=()", response.headers["permissions-policy"])

    def test_authentication_boundary_can_be_enabled(self):
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false", "COGNIX_JWT_SECRET": ""},
            clear=False,
        ):
            response = self.client.get("/sources")
            book_response = self.client.get("/brain/books")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "AUTH_REQUIRED")
        self.assertEqual(book_response.status_code, 401)
        self.assertEqual(book_response.json()["detail"]["code"], "AUTH_REQUIRED")

    def test_database_backed_ownership_scopes_sources_books_and_tasks(self):
        database = MemoryOwnershipDatabase()
        identity_patch = patch(
            "app.main.authenticate_request",
            side_effect=lambda request: {"sub": request.headers.get("x-test-user", "")},
        )
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), patch.object(store, "database", database), identity_patch:
            source_response = self.client.post(
                "/sources",
                json={"url": "https://example.com/persistent-owner"},
                headers={"x-test-user": "user-a"},
            )
            self.assertEqual(source_response.status_code, 201)
            source_id = source_response.json()["source"]["id"]
            self.assertEqual(database.source_owners[source_id], "user-a")
            self.assertEqual(
                self.client.get(f"/sources/{source_id}", headers={"x-test-user": "user-a"}).status_code,
                200,
            )
            self.assertEqual(
                self.client.get(f"/sources/{source_id}", headers={"x-test-user": "user-b"}).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    "/processing",
                    json={"source_id": source_id},
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )

            task_response = self.client.post(
                "/processing",
                json={"source_id": source_id},
                headers={"x-test-user": "user-a"},
            )
            task_id = task_response.json()["id"]
            self.assertEqual(task_response.status_code, 202)
            self.assertEqual(
                self.client.post(
                    f"/processing/{task_id}/advance",
                    headers={"x-test-user": "user-a"},
                ).status_code,
                200,
            )
            self.assertEqual(
                self.client.get(f"/processing/{task_id}", headers={"x-test-user": "user-b"}).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    f"/processing/{task_id}/advance",
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    f"/processing/{task_id}/retry",
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    f"/reviews/{source_id}/revision",
                    json={},
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    "/exports/google-drive",
                    json={"source_id": source_id, "idempotency_key": "foreign-source"},
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )

            book_response = self.client.post(
                "/brain/books",
                json={"title": "Persistent book", "text": "private persistent ownership"},
                headers={"x-test-user": "user-a"},
            )
            self.assertEqual(book_response.status_code, 201)
            book_id = book_response.json()["id"]
            self.assertEqual(database.book_owners[book_id], "user-a")
            self.assertEqual(
                self.client.get(f"/brain/books/{book_id}", headers={"x-test-user": "user-a"}).status_code,
                200,
            )
            self.assertEqual(
                self.client.get(f"/brain/books/{book_id}", headers={"x-test-user": "user-b"}).status_code,
                404,
            )
            other_user_search = self.client.get(
                f"/brain/books/{book_id}/search",
                params={"q": "persistent"},
                headers={"x-test-user": "user-b"},
            )
            self.assertEqual(other_user_search.status_code, 200)
            self.assertEqual(other_user_search.json()["total"], 0)
            self.assertEqual(
                self.client.get("/brain/books", headers={"x-test-user": "user-b"}).json()["total"],
                0,
            )
            self.assertEqual(
                self.client.get(
                    f"/brain/books/{book_id}/search",
                    params={"q": "persistent"},
                    headers={"x-test-user": "user-a"},
                ).json()["total"],
                1,
            )

    def test_unowned_database_records_remain_inaccessible(self):
        database = MemoryOwnershipDatabase()
        database.sources["legacy-source"] = {
            "id": "legacy-source", "url": "https://example.com/legacy", "claims": [],
        }
        database.books["legacy-book"] = {
            "id": "legacy-book", "title": "Legacy", "chapters": [], "updated_at": "2026-01-01",
        }
        identity_patch = patch(
            "app.main.authenticate_request",
            return_value={"sub": "user-a"},
        )
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), patch.object(store, "database", database), identity_patch:
            self.assertEqual(self.client.get("/sources/legacy-source").status_code, 404)
            self.assertEqual(self.client.get("/brain/books/legacy-book").status_code, 404)
            self.assertEqual(self.client.get("/sources").json()["total"], 0)
            self.assertEqual(self.client.get("/brain/books").json()["total"], 0)
        self.assertNotIn("legacy-source", database.source_owners)
        self.assertNotIn("legacy-book", database.book_owners)

    def test_brain_notes_concepts_and_graph_are_owner_scoped(self):
        database = MemoryOwnershipDatabase()
        identity_patch = patch(
            "app.main.authenticate_request",
            side_effect=lambda request: {"sub": request.headers.get("x-test-user", "")},
        )
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), patch.object(store, "database", database), identity_patch:
            headers_a = {"x-test-user": "user-a"}
            headers_b = {"x-test-user": "user-b"}
            created = self.client.post(
                "/brain/notes", json={"title": "Private note", "content": "owner A"}, headers=headers_a,
            )
            self.assertEqual(created.status_code, 201)
            note_id = created.json()["id"]
            self.assertEqual(database.brain_note_owners[note_id], "user-a")
            self.assertEqual(self.client.get("/brain/notes", headers=headers_a).json()["total"], 1)
            self.assertEqual(self.client.get("/brain/notes", headers=headers_b).json()["total"], 0)
            database.brain_notes["foreign-backlink"] = {
                "id": "foreign-backlink", "title": "Foreign backlink", "content": "private",
                "note_type": "note", "status": "draft", "updated_at": "2026-01-01",
                "sources": [{"source_type": "note", "source_id": note_id}],
            }
            database.brain_note_owners["foreign-backlink"] = "user-b"

            child = self.client.post(
                "/brain/notes",
                json={
                    "title": "Private backlink",
                    "content": "same-owner edge",
                    "source_type": "note",
                    "source_id": note_id,
                },
                headers=headers_a,
            )
            self.assertEqual(child.status_code, 201)
            self.assertEqual(
                self.client.get(f"/brain/notes/{note_id}/backlinks", headers=headers_a).json()["total"],
                1,
            )
            self.assertEqual(
                self.client.get(f"/brain/notes/{note_id}/backlinks", headers=headers_b).status_code,
                404,
            )
            cross_owner_note = self.client.post(
                "/brain/notes",
                json={
                    "title": "Invalid backlink",
                    "content": "must not link cross-owner",
                    "source_type": "note",
                    "source_id": note_id,
                },
                headers=headers_b,
            )
            self.assertEqual(cross_owner_note.status_code, 404)

            concept_a = self.client.post(
                "/brain/concepts", json={"name": "Private concept A"}, headers=headers_a,
            )
            concept_b = self.client.post(
                "/brain/concepts", json={"name": "Private concept B"}, headers=headers_a,
            )
            self.assertEqual(concept_a.status_code, 201)
            self.assertEqual(concept_b.status_code, 201)
            self.assertEqual(database.brain_concept_owners[concept_a.json()["id"]], "user-a")
            case_duplicate = self.client.post(
                "/brain/concepts", json={"name": "private CONCEPT a"}, headers=headers_a,
            )
            self.assertEqual(case_duplicate.status_code, 201)
            self.assertEqual(case_duplicate.json()["id"], concept_a.json()["id"])
            concept_b_user = self.client.post(
                "/brain/concepts", json={"name": "PRIVATE CONCEPT A"}, headers=headers_b,
            )
            self.assertEqual(concept_b_user.status_code, 201)
            self.assertNotEqual(concept_b_user.json()["id"], concept_a.json()["id"])
            link = self.client.post(
                "/brain/concept-links",
                json={
                    "from_concept_id": concept_a.json()["id"],
                    "to_concept_id": concept_b.json()["id"],
                    "relation": "related",
                },
                headers=headers_a,
            )
            self.assertEqual(link.status_code, 201)
            graph_a = self.client.get("/brain/graph", headers=headers_a).json()
            graph_b = self.client.get("/brain/graph", headers=headers_b).json()
            self.assertEqual(len(graph_a["nodes"]), 2)
            self.assertEqual(len(graph_a["edges"]), 1)
            self.assertEqual([node["id"] for node in graph_b["nodes"]], [concept_b_user.json()["id"]])
            self.assertEqual(graph_b["edges"], [])
            database.brain_concept_links["foreign-link"] = {
                "id": "foreign-link",
                "from_concept_id": concept_a.json()["id"],
                "to_concept_id": concept_b_user.json()["id"],
                "relation": "invalid-cross-owner",
                "weight": 1,
                "created_at": "2026-01-01",
            }
            self.assertEqual(len(self.client.get("/brain/graph", headers=headers_a).json()["edges"]), 1)
            self.assertEqual(len(self.client.get("/brain/graph", headers=headers_b).json()["edges"]), 0)
            self.assertEqual(self.client.get("/brain/concepts", headers=headers_b).json()["total"], 1)
            self.assertEqual(
                self.client.post(
                    "/brain/concept-links",
                    json={
                        "from_concept_id": concept_a.json()["id"],
                        "to_concept_id": concept_b.json()["id"],
                        "relation": "private",
                    },
                    headers=headers_b,
                ).status_code,
                404,
            )

    def test_legacy_unowned_brain_records_remain_inaccessible(self):
        database = MemoryOwnershipDatabase()
        database.brain_notes["legacy-note"] = {
            "id": "legacy-note", "title": "Legacy", "content": "private",
            "note_type": "note", "status": "draft", "updated_at": "2026-01-01", "sources": [],
        }
        database.brain_concepts["legacy-concept"] = {
            "id": "legacy-concept", "name": "Legacy", "description": None,
            "created_at": "2026-01-01", "updated_at": "2026-01-01",
        }
        database.language_cards["legacy-card"] = {
            "id": "legacy-card", "front": "legacy", "back": "private",
            "owner_id": None, "due_at": "2000-01-01T00:00:00+00:00",
            "stability": 0, "difficulty": 5, "reps": 0, "lapses": 0, "state": "learning",
        }
        identity_patch = patch("app.main.authenticate_request", return_value={"sub": "user-a"})
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), patch.object(store, "database", database), identity_patch:
            self.assertEqual(self.client.get("/brain/notes").json()["total"], 0)
            self.assertEqual(self.client.get("/brain/concepts").json()["total"], 0)
            self.assertEqual(self.client.get("/brain/graph").json(), {"nodes": [], "edges": []})
            self.assertEqual(self.client.get("/brain/notes/legacy-note/backlinks").status_code, 404)
            self.assertEqual(self.client.get("/brain/language/due").json()["total"], 0)
            self.assertEqual(
                self.client.post(
                    "/brain/language/cards/legacy-card/review",
                    json={"rating": 4},
                ).status_code,
                404,
            )

    def test_language_cards_are_owner_scoped_for_create_due_and_review(self):
        database = MemoryOwnershipDatabase()
        identity_patch = patch(
            "app.main.authenticate_request",
            side_effect=lambda request: {"sub": request.headers.get("x-test-user", "")},
        )
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), patch.object(store, "database", database), identity_patch:
            headers_a = {"x-test-user": "user-a"}
            headers_b = {"x-test-user": "user-b"}
            created = self.client.post(
                "/brain/language/cards",
                json={"front": "hello", "back": "greeting", "language": "en"},
                headers=headers_a,
            )
            self.assertEqual(created.status_code, 201)
            card_id = created.json()["id"]
            self.assertEqual(database.language_cards[card_id]["owner_id"], "user-a")
            self.assertEqual(self.client.get("/brain/language/due", headers=headers_a).json()["total"], 1)
            self.assertEqual(self.client.get("/brain/language/due", headers=headers_b).json()["total"], 0)
            self.assertEqual(
                self.client.post(
                    f"/brain/language/cards/{card_id}/review",
                    json={"rating": 4},
                    headers=headers_b,
                ).status_code,
                404,
            )
            self.assertEqual(database.language_cards[card_id]["reps"], 0)
            reviewed = self.client.post(
                f"/brain/language/cards/{card_id}/review",
                json={"rating": 4},
                headers=headers_a,
            )
            self.assertEqual(reviewed.status_code, 200)
            self.assertEqual(database.language_cards[card_id]["reps"], 1)

    def test_brain_ownership_endpoints_reject_unauthenticated_requests(self):
        identity_patch = patch("app.main.authenticate_request", return_value={})
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), identity_patch:
            self.assertEqual(self.client.get("/brain/notes").status_code, 401)
            self.assertEqual(self.client.get("/brain/concepts").status_code, 401)
            self.assertEqual(self.client.get("/brain/graph").status_code, 401)
            self.assertEqual(self.client.get("/brain/language/due").status_code, 401)

    def test_source_access_is_scoped_to_authenticated_owner(self):
        identity_patch = patch(
            "app.main.authenticate_request",
            side_effect=lambda request: {"sub": request.headers.get("x-test-user", "")},
        )
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), identity_patch:
            created = self.client.post(
                "/sources",
                json={"url": "https://example.com/user-owned-source"},
                headers={"x-test-user": "user-a"},
            )
            self.assertEqual(created.status_code, 201)
            source_id = created.json()["source"]["id"]

            self.assertEqual(
                self.client.get(f"/sources/{source_id}", headers={"x-test-user": "user-a"}).status_code,
                200,
            )
            self.assertEqual(
                self.client.get(f"/sources/{source_id}", headers={"x-test-user": "user-b"}).status_code,
                404,
            )
            user_b_sources = self.client.get("/sources", headers={"x-test-user": "user-b"})
            self.assertEqual(user_b_sources.json()["total"], 0)
            self.assertEqual(
                self.client.patch(
                    f"/sources/{source_id}/translation",
                    json={"human_edited_myanmar": "Unauthorized edit"},
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )

    def test_book_access_and_book_search_are_scoped_to_authenticated_owner(self):
        identity_patch = patch(
            "app.main.authenticate_request",
            side_effect=lambda request: {"sub": request.headers.get("x-test-user", "")},
        )
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), identity_patch:
            created = self.client.post(
                "/brain/books",
                json={"title": "Private book", "text": "private zebra ownership phrase"},
                headers={"x-test-user": "user-a"},
            )
            self.assertEqual(created.status_code, 201)
            book_id = created.json()["id"]

            self.assertEqual(
                self.client.get(f"/brain/books/{book_id}", headers={"x-test-user": "user-a"}).status_code,
                200,
            )
            self.assertEqual(
                self.client.get(f"/brain/books/{book_id}", headers={"x-test-user": "user-b"}).status_code,
                404,
            )
            self.assertEqual(
                self.client.get(
                    f"/brain/books/{book_id}/search",
                    params={"q": "zebra"},
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )
            user_b_books = self.client.get("/brain/books", headers={"x-test-user": "user-b"})
            self.assertEqual(user_b_books.json()["total"], 0)
            self.assertEqual(
                self.client.get(
                    "/brain/query",
                    params={"q": "zebra"},
                    headers={"x-test-user": "user-b"},
                ).json()["total"],
                0,
            )

    def test_processing_task_access_is_scoped_through_its_source(self):
        identity_patch = patch(
            "app.main.authenticate_request",
            side_effect=lambda request: {"sub": request.headers.get("x-test-user", "")},
        )
        with patch.dict(
            "os.environ",
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_DEV_MODE": "false"},
            clear=False,
        ), identity_patch:
            source_response = self.client.post(
                "/sources",
                json={"url": "https://example.com/user-owned-task-source"},
                headers={"x-test-user": "user-a"},
            )
            source_id = source_response.json()["source"]["id"]
            task_response = self.client.post(
                "/processing",
                json={"source_id": source_id},
                headers={"x-test-user": "user-a"},
            )
            self.assertEqual(task_response.status_code, 202)
            task_id = task_response.json()["id"]

            advanced = self.client.post(
                f"/processing/{task_id}/advance",
                headers={"x-test-user": "user-a"},
            )
            self.assertEqual(advanced.status_code, 200)
            self.assertEqual(advanced.json()["stage"], "extracting")

            self.assertEqual(
                self.client.get(f"/processing/{task_id}", headers={"x-test-user": "user-a"}).status_code,
                200,
            )
            self.assertEqual(
                self.client.get(f"/processing/{task_id}", headers={"x-test-user": "user-b"}).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    "/processing",
                    json={"source_id": source_id},
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    f"/processing/{task_id}/advance",
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    f"/processing/{task_id}/retry",
                    headers={"x-test-user": "user-b"},
                ).status_code,
                404,
            )
            self.assertEqual(store.tasks[task_id]["stage"], "extracting")

    def test_language_schedule_handles_learning_and_lapse(self):
        card = {
            "stability": 2.0,
            "difficulty": 5.0,
            "reps": 1,
            "lapses": 0,
        }
        stable = _schedule(card, 4)
        self.assertGreater(stable[0], card["stability"])
        self.assertEqual(stable[2], 2)
        self.assertEqual(stable[4], "review")
        lapse = _schedule(card, 1)
        self.assertEqual(lapse[2], 0)
        self.assertEqual(lapse[3], 1)
        self.assertEqual(lapse[4], "relearning")

    def test_optional_advanced_services_fail_closed_without_persistence(self):
        self.assertIsNone(store.database)
        for method, path, kwargs in (
            ("post", "/brain/embeddings/index", {"json": {"owner_type": "chunk", "owner_ids": ["missing"]}}),
            ("post", "/brain/query/semantic", {"json": {"q": "recall"}}),
            ("post", "/brain/language/cards", {"json": {"front": "hello", "back": "မင်္ဂလာပါ", "language": "my"}}),
            ("post", "/brain/vault/items", {"json": {"label": "test", "ciphertext": "ct", "nonce": "n", "kdf_salt": "s", "kdf_params": {}}}),
            ("post", "/brain/documents/ocr", {"files": {"file": ("note.txt", b"not supported", "text/plain")}}),
            ("post", "/brain/media/ingest", {"files": {"file": ("note.txt", b"not supported", "text/plain")}}),
        ):
            response = getattr(self.client, method)(path, **kwargs)
            self.assertIn(response.status_code, {400, 401, 503}, path)

    def test_agent_mode_requires_persistent_database(self):
        response = self.client.post(
            "/brain/agent/jobs",
            json={"question": "test", "idempotency_key": "agent-test-1"},
        )
        self.assertEqual(response.status_code, 503)

    def test_readiness_requires_database_when_configured(self):
        with patch.dict("app.main.__dict__", {"REQUIRE_DATABASE": True, "store": store}):
            response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "not_ready")
        self.assertTrue(response.json()["database_required"])

    def test_worker_advances_queued_processing(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/worker"}
        ).json()["source"]
        task = self.client.post("/processing", json={"source_id": source["id"]}).json()

        processed = run_once()

        self.assertEqual(processed, 1)
        refreshed = self.client.get(f"/processing/{task['id']}")
        self.assertEqual(refreshed.json()["stage"], "extracting")
        self.assertEqual(refreshed.json()["status"], "running")


if __name__ == "__main__":
    unittest.main()
