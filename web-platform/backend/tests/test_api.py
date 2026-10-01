import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.store import store
from app.worker import run_once
from app.services.research_processor import ProcessingResult
from app.routers.brain_advanced import _schedule


class CognixApiTests(unittest.TestCase):
    def setUp(self):
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
        store.tasks.clear()
        store.reviews.clear()
        store.exports.clear()
        store.activity.clear()
        store.export_keys.clear()
        store.brain_books.clear()
        store.brain_notes.clear()
        store.brain_concepts.clear()
        store.brain_concept_links.clear()
        self.client = TestClient(app)

    def test_health_and_root_metadata(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        root = self.client.get("/")
        self.assertEqual(root.status_code, 200)
        self.assertEqual(root.json()["service"], "cognix-core-api")
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
            {"COGNIX_AUTH_REQUIRED": "true", "COGNIX_JWT_SECRET": ""},
            clear=False,
        ):
            response = self.client.get("/sources")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "AUTH_REQUIRED")

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
            self.assertIn(response.status_code, {400, 503}, path)

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
