import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg

from app.persistence import Database


@unittest.skipUnless(os.getenv("DATABASE_URL"), "DATABASE_URL required for integration tests")
class DatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ["DATABASE_URL"]
        database = Database(cls.dsn)
        database.ensure_schema()
        database.close()
        with psycopg.connect(cls.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processing_tasks (
                        id TEXT PRIMARY KEY,
                        stage TEXT NOT NULL DEFAULT 'extracting',
                        progress INTEGER NOT NULL DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'queued',
                        retry_count INTEGER NOT NULL DEFAULT 0,
                        error TEXT,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        claimed_by TEXT,
                        claimed_at TIMESTAMPTZ
                    )
                    """
                )
                for statement in (
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS stage TEXT NOT NULL DEFAULT 'extracting'",
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS progress INTEGER NOT NULL DEFAULT 0",
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'queued'",
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0",
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS error TEXT",
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()",
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS claimed_by TEXT",
                    "ALTER TABLE processing_tasks ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ",
                ):
                    cur.execute(statement)
                cur.execute(
                    """INSERT INTO processing_tasks(id,status,stage,retry_count)
                       VALUES ('integration-task','queued','extracting',0)
                       ON CONFLICT (id) DO UPDATE SET status='queued',stage='extracting',
                         retry_count=0,claimed_by=NULL,claimed_at=NULL,updated_at=now()"""
                )
            conn.commit()

    def setUp(self):
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE processing_tasks
                       SET status='queued',stage='extracting',retry_count=0,
                           claimed_by=NULL,claimed_at=NULL,updated_at=now()
                       WHERE id='integration-task'"""
                )
            conn.commit()

    def _create_book(self):
        book_id = f"lease-book-{uuid4().hex}"
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO books(
                           id,title,file_type,source_kind,status,processing_stage,
                           processing_attempts,original_filename
                       ) VALUES (%s,'Lease test','pdf','upload','queued','queued',0,'lease-test.pdf')""",
                    (book_id,),
                )
            conn.commit()
        self.addCleanup(self._delete_book, book_id)
        return book_id

    def _delete_book(self, book_id):
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """DELETE FROM embeddings WHERE owner_type='chunk' AND owner_id IN (
                           SELECT c.id FROM chunks c
                           JOIN chapters ch ON ch.id=c.chapter_id
                           WHERE ch.book_id=%s
                       )""",
                    (book_id,),
                )
                cur.execute("DELETE FROM books WHERE id=%s", (book_id,))
            conn.commit()

    def _create_export(self):
        suffix = uuid4().hex
        source_id = f"lease-source-{suffix}"
        export_id = f"lease-export-{suffix}"
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO sources(id,url,status,processing_stage)
                       VALUES (%s,%s,'approved','approved')""",
                    (source_id, f"https://lease-test.invalid/{suffix}"),
                )
                cur.execute(
                    """INSERT INTO export_jobs(
                           id,source_id,destination,status,idempotency_key
                       ) VALUES (%s,%s,'google_drive','queued',%s)""",
                    (export_id, source_id, f"lease-key-{suffix}"),
                )
            conn.commit()
        self.addCleanup(self._delete_export, export_id, source_id)
        return export_id

    def _delete_export(self, export_id, source_id):
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM export_jobs WHERE id=%s", (export_id,))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
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

    def test_active_lease_is_not_stolen_and_only_token_can_renew_or_transition(self):
        db_a = Database(self.dsn)
        db_b = Database(self.dsn)
        token_a = None
        try:
            token_a = db_a.claim_task("integration-task")
            self.assertIsNotNone(token_a)
            self.assertIsNone(db_b.claim_task("integration-task"))
            self.assertFalse(db_b.renew_task_claim("integration-task", "different-token"))
            self.assertTrue(db_a.renew_task_claim("integration-task", token_a))

            task = {
                "id": "integration-task", "stage": "failed", "progress": 0,
                "status": "failed", "retry_count": 0, "error": "failure",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
            self.assertFalse(
                db_b.save_processing_transition(
                    task,
                    {"id": "nonexistent-source"},
                    None,
                    "running",
                    "extracting",
                    "different-token",
                )
            )
        finally:
            db_a.release_task("integration-task", token_a)
            db_a._pool.close()
            db_b._pool.close()

    def test_stale_lease_is_recovered_with_a_new_fencing_token(self):
        db_a = Database(self.dsn)
        db_b = Database(self.dsn)
        old_token = None
        try:
            old_token = db_a.claim_task("integration-task")
            self.assertIsNotNone(old_token)
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE processing_tasks
                           SET claimed_at=now() - interval '31 minutes'
                           WHERE id='integration-task'"""
                    )
                conn.commit()

            new_token = db_b.claim_task("integration-task")
            self.assertIsNotNone(new_token)
            self.assertNotEqual(old_token, new_token)
            self.assertFalse(db_a.renew_task_claim("integration-task", old_token))
            self.assertFalse(db_a.release_task("integration-task", old_token))
            self.assertTrue(db_b.release_task("integration-task", new_token))
        finally:
            db_a._pool.close()
            db_b._pool.close()

    def test_completed_task_cannot_be_reclaimed(self):
        db = Database(self.dsn)
        try:
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE processing_tasks
                           SET status='completed',stage='needs_review',
                               claimed_by=NULL,claimed_at=NULL
                           WHERE id='integration-task'"""
                    )
                conn.commit()
            self.assertIsNone(db.claim_task("integration-task"))
        finally:
            db._pool.close()

    def test_connection_is_returned_to_pool(self):
        db = Database(self.dsn)
        try:
            for _ in range(20):
                self.assertTrue(db.ping())
            self.assertLessEqual(db._pool.get_stats()["pool_available"], db._pool.max_size)
        finally:
            db._pool.close()

    def test_book_job_claim_is_atomic_fenced_and_terminal_safe(self):
        book_id = self._create_book()
        db_a, db_b = Database(self.dsn), Database(self.dsn)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                claims = list(pool.map(
                    lambda db: db.claim_book_processing(book_id),
                    (db_a, db_b),
                ))
            winners = [claim for claim in claims if claim is not None]
            self.assertEqual(len(winners), 1)
            old_book, old_token = winners[0]
            current_db = db_a if claims[0] is not None else db_b
            other_db = db_b if current_db is db_a else db_a
            self.assertIsNone(other_db.claim_book_processing(book_id))

            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE books
                           SET processing_claimed_at=now()-interval '31 minutes',
                               processing_started_at=now()-interval '31 minutes'
                           WHERE id=%s""",
                        (book_id,),
                    )
                conn.commit()
            reclaimed = other_db.claim_book_processing(book_id)
            self.assertIsNotNone(reclaimed)
            book, new_token = reclaimed
            self.assertNotEqual(old_token, new_token)
            self.assertFalse(current_db.renew_book_processing_claim(book_id, old_token))
            self.assertFalse(current_db.fail_book_processing(book_id, old_token, "stale"))
            self.assertFalse(current_db.release_book_claim(book_id, old_token))
            self.assertFalse(current_db.complete_book_extraction(
                book_id, old_token, "Stale", None, [], []
            ))
            self.assertTrue(other_db.renew_book_processing_claim(book_id, new_token))
            self.assertTrue(other_db.complete_book_extraction(
                book_id, new_token, "Completed", None, [], []
            ))
            self.assertIsNone(other_db.claim_book_processing(book_id))
            self.assertFalse(other_db.release_book_claim(book_id, new_token))
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE books SET status='ready',processing_stage='completed'
                           WHERE id=%s""",
                        (book_id,),
                    )
                conn.commit()
            self.assertIsNone(other_db.claim_book_processing(book_id))
            self.assertIsNone(other_db.claim_book_finalization(book_id))
        finally:
            db_a._pool.close()
            db_b._pool.close()

    def test_book_job_current_token_can_fail_and_release(self):
        book_id = self._create_book()
        db = Database(self.dsn)
        try:
            claimed = db.claim_book_processing(book_id)
            self.assertIsNotNone(claimed)
            _, token = claimed
            self.assertTrue(db.fail_book_processing(book_id, token, "expected test failure"))
            self.assertIsNone(db.claim_book_processing(book_id))

            releasable_id = self._create_book()
            releasable = db.claim_book_processing(releasable_id)
            self.assertIsNotNone(releasable)
            _, release_token = releasable
            self.assertTrue(db.release_book_claim(releasable_id, release_token))
        finally:
            db._pool.close()

    def test_book_finalization_lease_is_exclusive_and_fenced(self):
        book_id = self._create_book()
        chapter_id = f"lease-chapter-{uuid4().hex}"
        chunk_id = f"lease-chunk-{uuid4().hex}"
        embedding_id = f"lease-embedding-{uuid4().hex}"
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books SET status='processing',processing_stage='embedding'
                       WHERE id=%s""",
                    (book_id,),
                )
                cur.execute(
                    """INSERT INTO chapters(id,book_id,chapter_number,title)
                       VALUES (%s,%s,1,'Lease test')""",
                    (chapter_id, book_id),
                )
                cur.execute(
                    """INSERT INTO chunks(id,chapter_id,sequence,content)
                       VALUES (%s,%s,1,'Lease test content')""",
                    (chunk_id, chapter_id),
                )
                cur.execute(
                    """INSERT INTO embeddings(id,owner_type,owner_id,content)
                       VALUES (%s,'chunk',%s,'Lease test content')""",
                    (embedding_id, chunk_id),
                )
            conn.commit()
        db_a, db_b = Database(self.dsn), Database(self.dsn)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                tokens = list(pool.map(
                    lambda db: db.claim_book_finalization(book_id),
                    (db_a, db_b),
                ))
            winner = [token for token in tokens if token is not None]
            self.assertEqual(len(winner), 1)
            current_db = db_a if tokens[0] is not None else db_b
            other_db = db_b if current_db is db_a else db_a
            self.assertIsNone(other_db.claim_book_finalization(book_id))
            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE books SET processing_claimed_at=now()-interval '31 minutes'
                           WHERE id=%s""",
                        (book_id,),
                    )
                conn.commit()
            reclaimed = other_db.claim_book_finalization(book_id)
            self.assertIsNotNone(reclaimed)
            self.assertNotEqual(winner[0], reclaimed)
            self.assertFalse(current_db.complete_book_finalization(book_id, winner[0]))
            self.assertTrue(other_db.complete_book_finalization(book_id, reclaimed))
            self.assertIsNone(other_db.claim_book_finalization(book_id))
        finally:
            db_a._pool.close()
            db_b._pool.close()

    def test_export_job_claim_is_atomic_fenced_and_terminal_safe(self):
        export_id = self._create_export()
        db_a, db_b = Database(self.dsn), Database(self.dsn)
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                claims = list(pool.map(
                    lambda db: db.claim_export_job(export_id),
                    (db_a, db_b),
                ))
            winners = [claim for claim in claims if claim is not None]
            self.assertEqual(len(winners), 1)
            _, old_token = winners[0]
            current_db = db_a if claims[0] is not None else db_b
            other_db = db_b if current_db is db_a else db_a
            self.assertIsNone(other_db.claim_export_job(export_id))
            self.assertIsNotNone(current_db.transition_export_job(
                export_id, old_token, "queued", "uploading"
            ))

            with psycopg.connect(self.dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE export_jobs SET claimed_at=now()-interval '31 minutes'
                           WHERE id=%s""",
                        (export_id,),
                    )
                conn.commit()
            reclaimed = other_db.claim_export_job(export_id)
            self.assertIsNotNone(reclaimed)
            _, new_token = reclaimed
            self.assertNotEqual(old_token, new_token)
            self.assertFalse(current_db.renew_export_job_claim(export_id, old_token))
            self.assertIsNone(current_db.transition_export_job(
                export_id, old_token, "uploading", "exported", "stale"
            ))
            self.assertIsNone(current_db.transition_export_job(
                export_id, old_token, "uploading", "failed", error="stale"
            ))
            self.assertFalse(current_db.release_export_job_claim(export_id, old_token))
            self.assertTrue(other_db.renew_export_job_claim(export_id, new_token))
            self.assertIsNotNone(other_db.transition_export_job(
                export_id, new_token, "uploading", "exported", "https://example.test/result"
            ))
            self.assertFalse(other_db.release_export_job_claim(export_id, new_token))
            self.assertIsNone(other_db.claim_export_job(export_id))
        finally:
            db_a._pool.close()
            db_b._pool.close()

    def test_export_job_current_token_can_fail_and_release(self):
        export_id = self._create_export()
        db = Database(self.dsn)
        try:
            claimed = db.claim_export_job(export_id)
            self.assertIsNotNone(claimed)
            _, token = claimed
            self.assertIsNotNone(db.transition_export_job(
                export_id, token, "queued", "failed", error="expected test failure"
            ))
            self.assertIsNone(db.claim_export_job(export_id))

            releasable_id = self._create_export()
            releasable = db.claim_export_job(releasable_id)
            self.assertIsNotNone(releasable)
            _, release_token = releasable
            self.assertTrue(db.release_export_job_claim(releasable_id, release_token))
        finally:
            db._pool.close()


if __name__ == "__main__":
    unittest.main()
