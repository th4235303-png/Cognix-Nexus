import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.store import store

class CognixApiTests(unittest.TestCase):
    def setUp(self):
        store.sources.clear(); store.tasks.clear(); store.reviews.clear(); store.exports.clear(); store.activity.clear(); store.export_keys.clear()
        self.client = TestClient(app)

    def test_duplicate_and_processing(self):
        first = self.client.post("/sources", json={"url":"https://example.com/research"})
        self.assertEqual(first.status_code, 201)
        source = first.json()["source"]
        duplicate = self.client.post("/sources", json={"url":"https://example.com/research/"})
        self.assertEqual(duplicate.json()["status"], "duplicate_ignored")
        task = self.client.post("/processing", json={"source_id":source["id"]})
        self.assertEqual(task.status_code, 202)
        advanced = self.client.post(f"/processing/{task.json()['id']}/advance")
        self.assertEqual(advanced.status_code, 200)
        self.assertEqual(advanced.json()['stage'], 'extracting')

    def test_approved_only_export_and_idempotency(self):
        source = self.client.post("/sources", json={"url":"https://example.com/approved"}).json()["source"]
        blocked = self.client.post("/exports/google-drive", json={"source_id":source["id"],"idempotency_key":"key-1"})
        self.assertEqual(blocked.status_code, 409)
        self.client.post(f"/reviews/{source['id']}/approve", json={})
        exported = self.client.post("/exports/google-drive", json={"source_id":source["id"],"idempotency_key":"key-1"})
        replay = self.client.post("/exports/google-drive", json={"source_id":source["id"],"idempotency_key":"key-1"})
        self.assertEqual(exported.status_code, 202)
        self.assertEqual(replay.json()["id"], exported.json()["id"])

if __name__ == "__main__":
    unittest.main()
