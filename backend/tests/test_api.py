import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.store import store


class CognixApiTests(unittest.TestCase):
    def setUp(self):
        store.sources.clear()
        store.tasks.clear()
        store.reviews.clear()
        store.exports.clear()
        store.activity.clear()
        store.export_keys.clear()
        self.client = TestClient(app)

    def test_health_and_root_metadata(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        root = self.client.get("/")
        self.assertEqual(root.status_code, 200)
        self.assertEqual(root.json()["service"], "cognix-core-api")

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

    def test_critical_warning_blocks_approval(self):
        source = self.client.post(
            "/sources", json={"url": "https://example.com/warning"}
        ).json()["source"]
        store.sources[source["id"]]["critical_warnings"] = ["Missing citation"]

        blocked = self.client.post(f"/reviews/{source['id']}/approve", json={})
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["detail"]["code"], "CRITICAL_WARNINGS")
        self.assertEqual(store.sources[source["id"]]["status"], "new")

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


if __name__ == "__main__":
    unittest.main()
