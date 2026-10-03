import os
import unittest
from concurrent.futures import ThreadPoolExecutor

import psycopg

from app.persistence import Database


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL required for integration tests")
class DatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ["DATABASE_URL"]
        with psycopg.connect(cls.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processing_tasks (
                        id TEXT PRIMARY KEY,
                        claimed_by TEXT,
                        claimed_at TIMESTAMPTZ
                    )
                    """
                )
                cur.execute("DELETE FROM processing_tasks")
                cur.execute("INSERT INTO processing_tasks(id) VALUES ('integration-task')")
            conn.commit()

    def test_pool_and_atomic_claim(self):
        db_a = Database(self.dsn)
        db_b = Database(self.dsn)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda db: db.try_claim_task("integration-task"),
                    (db_a, db_b),
                ))
            self.assertEqual(sorted(results), [False, True])
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT claimed_by FROM processing_tasks WHERE id='integration-task'")
                    self.assertIsNotNone(cur.fetchone()[0])
            db_a.release_task("integration-task")
            db_b.release_task("integration-task")
        finally:
            db_a._pool.close()
            db_b._pool.close()

    def test_connection_is_returned_to_pool(self):
        db = Database(self.dsn)
        try:
            for _ in range(20):
                self.assertTrue(db.ping())
            self.assertLessEqual(db._pool.get_stats()["pool_available"], db._pool.max_size)
        finally:
            db._pool.close()


if __name__ == "__main__":
    unittest.main()
