import unittest

from app.persistence import Database


class RecordingCursor:
    def __init__(self, one_results=None, all_results=None):
        self.one_results = list(one_results or [])
        self.all_results = list(all_results or [])
        self.statements = []
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.statements.append((query, params))

    def fetchone(self):
        return self.one_results.pop(0) if self.one_results else None

    def fetchall(self):
        return self.all_results.pop(0) if self.all_results else []


class RecordingConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self._cursor

    def commit(self):
        pass


def database_with_cursor(cursor):
    database = Database.__new__(Database)
    connection = RecordingConnection(cursor)
    database.connect = lambda: connection
    database.worker_id = "worker-test"
    database._claim_tokens = {}
    return database


class PersistenceOwnershipTests(unittest.TestCase):
    def test_new_tasks_start_queued_and_cannot_overwrite_existing_task_ids(self):
        cursor = RecordingCursor(one_results=[{"id": "task-a"}])
        database = database_with_cursor(cursor)
        queued_task = {
            "id": "task-a", "source_id": "source-a", "stage": "queued",
            "progress": 0, "status": "queued", "retry_count": 0,
            "error": None, "created_at": "now", "updated_at": "now",
        }
        database.save_task(queued_task)
        query, _ = cursor.statements[0]
        self.assertIn("ON CONFLICT (id) DO NOTHING", query)
        self.assertIn("RETURNING id", query)

        with self.assertRaises(ValueError):
            database.save_task({**queued_task, "status": "running"})

    def test_claim_requires_runnable_due_unclaimed_task(self):
        cursor = RecordingCursor(one_results=[{"id": "task-a"}])
        database = database_with_cursor(cursor)

        token = database.claim_task("task-a")

        self.assertTrue(token.startswith("worker-test:"))
        query, params = cursor.statements[0]
        self.assertIn("status IN ('queued', 'running')", query)
        self.assertIn("stage NOT IN ('needs_review', 'approved')", query)
        self.assertIn("claimed_by IS NULL OR claimed_at IS NULL", query)
        self.assertIn("claimed_at < now() - interval '30 minutes'", query)
        self.assertIn("updated_at <= now() - make_interval", query)
        self.assertEqual(params, (token, "task-a"))

    def test_claim_renewal_and_release_require_exact_current_token(self):
        cursor = RecordingCursor(one_results=[{"id": "task-a"}, {"id": "task-a"}])
        database = database_with_cursor(cursor)
        database._claim_tokens["task-a"] = "worker-test:current"

        self.assertTrue(database.renew_task_claim("task-a", "worker-test:current"))
        renew_query, renew_params = cursor.statements[0]
        self.assertIn("claimed_by=%s", renew_query)
        self.assertIn("claimed_at >= now() - interval '30 minutes'", renew_query)
        self.assertEqual(renew_params, ("task-a", "worker-test:current"))

        self.assertTrue(database.release_task("task-a"))
        release_query, release_params = cursor.statements[1]
        self.assertIn("claimed_by=%s", release_query)
        self.assertEqual(release_params, ("task-a", "worker-test:current"))
        self.assertNotIn("task-a", database._claim_tokens)

    def test_non_owner_cannot_persist_task_failure_or_transition(self):
        cursor = RecordingCursor()
        database = database_with_cursor(cursor)
        task = {
            "id": "task-a", "stage": "failed", "progress": 0, "status": "failed",
            "retry_count": 0, "error": "failure", "updated_at": "now",
        }

        self.assertFalse(
            database.save_processing_transition(
                task, {"id": "source-a"}, None, "running", "extracting", "old-worker:token"
            )
        )
        query, params = cursor.statements[0]
        self.assertIn("WHERE id=%s AND claimed_by=%s", query)
        self.assertIn("status=%s AND stage=%s", query)
        self.assertIn("claimed_at >= now() - interval '30 minutes'", query)
        self.assertEqual(params[-4:], ("task-a", "old-worker:token", "running", "extracting"))

    def test_source_and_task_lookups_scope_to_source_owner(self):
        cursor = RecordingCursor()
        database = database_with_cursor(cursor)

        self.assertIsNone(database.get_source_for_owner("source-a", "user-b"))
        source_query, source_params = cursor.statements[0]
        self.assertIn("id=%s AND owner_id=%s", source_query)
        self.assertEqual(source_params, ("source-a", "user-b"))

        self.assertIsNone(database.get_task_for_owner("task-a", "user-b"))
        task_query, task_params = cursor.statements[1]
        self.assertIn("JOIN sources s ON s.id=t.source_id", task_query)
        self.assertIn("s.owner_id=%s", task_query)
        self.assertEqual(task_params, ("task-a", "user-b"))

    def test_book_lookup_and_search_scope_by_owner(self):
        cursor = RecordingCursor()
        database = database_with_cursor(cursor)

        self.assertIsNone(database.get_book("book-a", "user-b"))
        book_query, book_params = cursor.statements[0]
        self.assertIn("id=%s AND owner_id=%s", book_query)
        self.assertEqual(book_params, ("book-a", "user-b"))

        database.search_book("book-a", "private", owner_id="user-b")
        search_query, search_params = cursor.statements[1]
        self.assertIn("JOIN books b ON b.id=ch.book_id", search_query)
        self.assertIn("b.owner_id=%s", search_query)
        self.assertEqual(search_params, ("book-a", "user-b", "%private%", 20))

    def test_book_lists_and_task_lists_scope_by_owner(self):
        cursor = RecordingCursor(one_results=[{"total": 0}])
        database = database_with_cursor(cursor)

        self.assertEqual(database.list_books(owner_id="user-b"), ([], 0))
        count_query, count_params = cursor.statements[0]
        books_query, books_params = cursor.statements[1]
        self.assertIn("WHERE owner_id=%s", count_query)
        self.assertEqual(count_params, ("user-b",))
        self.assertIn("WHERE b.owner_id=%s", books_query)
        self.assertEqual(books_params, ("user-b", 50, 0))

        self.assertEqual(database.list_tasks_for_owner("user-b"), [])
        tasks_query, task_params = cursor.statements[2]
        self.assertIn("JOIN sources s ON s.id=t.source_id", tasks_query)
        self.assertIn("WHERE s.owner_id=%s", tasks_query)
        self.assertEqual(task_params, ("user-b",))

    def test_new_records_persist_owner_without_changing_owner_on_update(self):
        cursor = RecordingCursor(one_results=[{"id": "source-a"}, {"id": "book-a"}])
        database = database_with_cursor(cursor)
        source = {
            "id": "source-a", "url": "https://example.test", "status": "new",
            "processing_stage": "queued", "source_trust": "unverified",
            "original_text": None, "ai_summary": None, "myanmar_translation": None,
            "human_edited_myanmar": None, "approved_myanmar": None, "note": None,
            "critical_warnings": [], "key_points": [], "created_at": "2026-01-01",
            "updated_at": "2026-01-01", "claims": [],
        }
        database.save_source(source, "user-a")
        source_query, source_params = cursor.statements[0]
        self.assertIn("key_points, owner_id, created_at", source_query)
        self.assertIn("owner_id", source_params)
        self.assertEqual(source_params["owner_id"], "user-a")
        self.assertNotIn("owner_id=EXCLUDED.owner_id", source_query)

        book = {
            "id": "book-a", "title": "Book", "author": None, "language": "en",
            "file_type": "text", "source_kind": "imported_text", "source_url": None,
            "status": "ready", "description": None, "content_hash": "hash",
            "created_at": "2026-01-01", "updated_at": "2026-01-01", "chapters": [],
        }
        database.save_brain_book(book, "user-a")
        book_query, book_params = cursor.statements[2]
        self.assertIn("description, content_hash, owner_id, binary_storage", book_query)
        self.assertEqual(book_params["owner_id"], "user-a")
        self.assertNotIn("owner_id=EXCLUDED.owner_id", book_query)

    def test_note_and_concept_lookups_scope_by_owner(self):
        cursor = RecordingCursor(one_results=[None, None, {"id": "target"}])
        database = database_with_cursor(cursor)

        self.assertEqual(database.list_brain_notes_for_owner("user-b"), [])
        list_query, list_params = cursor.statements[0]
        self.assertIn("FROM notes WHERE owner_id=%s", list_query)
        self.assertEqual(list_params, ("user-b",))

        self.assertIsNone(database.get_brain_note_for_owner("note-a", "user-b"))
        note_query, note_params = cursor.statements[1]
        self.assertIn("id=%s AND owner_id=%s", note_query)
        self.assertEqual(note_params, ("note-a", "user-b"))

        self.assertIsNone(database.get_brain_concept_for_owner("concept-a", "user-b"))
        concept_query, concept_params = cursor.statements[2]
        self.assertIn("id=%s AND owner_id=%s", concept_query)
        self.assertEqual(concept_params, ("concept-a", "user-b"))

        self.assertEqual(database.list_note_backlinks_for_owner("note-a", "user-b"), [])
        target_query, target_params = cursor.statements[3]
        backlinks_query, backlinks_params = cursor.statements[4]
        self.assertIn("id=%s AND owner_id=%s", target_query)
        self.assertEqual(target_params, ("note-a", "user-b"))
        self.assertIn("ns.source_id=%s AND n.owner_id=%s", backlinks_query)
        self.assertEqual(backlinks_params, ("note-a", "user-b"))

    def test_concept_graph_scopes_both_linked_concepts(self):
        cursor = RecordingCursor()
        database = database_with_cursor(cursor)

        self.assertEqual(database.list_concept_links_for_owner("user-a"), [])
        query, params = cursor.statements[0]
        self.assertIn("JOIN concepts source ON source.id=l.from_concept_id", query)
        self.assertIn("JOIN concepts target ON target.id=l.to_concept_id", query)
        self.assertIn("source.owner_id=%s AND target.owner_id=%s", query)
        self.assertEqual(params, ("user-a", "user-a"))

    def test_concept_name_lookup_uses_database_normalization_and_owner(self):
        cursor = RecordingCursor()
        database = database_with_cursor(cursor)

        self.assertIsNone(database.get_brain_concept_by_name_for_owner("Concept", "user-a"))
        query, params = cursor.statements[0]
        self.assertIn("owner_id=%s AND lower(name)=lower(%s)", query)
        self.assertEqual(params, ("user-a", "Concept"))

        self.assertIsNone(database.get_brain_concept_by_name_for_owner("Concept", None))
        legacy_query, legacy_params = cursor.statements[1]
        self.assertIn("lower(name)=lower(%s)", legacy_query)
        self.assertNotIn("owner_id=%s", legacy_query)
        self.assertEqual(legacy_params, ("Concept",))

    def test_new_notes_concepts_and_links_persist_and_enforce_owner(self):
        cursor = RecordingCursor(one_results=[{"id": "note-a"}, {"id": "concept-a"}, {"id": "link-a"}])
        database = database_with_cursor(cursor)
        note = {
            "id": "note-a", "title": "Note", "content": "private", "note_type": "note",
            "status": "draft", "created_at": "2026-01-01", "updated_at": "2026-01-01",
        }
        database.save_brain_note(note, "user-a")
        note_query, note_params = cursor.statements[0]
        self.assertIn("owner_id", note_query)
        self.assertEqual(note_params["owner_id"], "user-a")
        self.assertIn("notes.owner_id IS NOT DISTINCT FROM EXCLUDED.owner_id", note_query)

        concept = {
            "id": "concept-a", "name": "Concept", "description": None,
            "created_at": "2026-01-01", "updated_at": "2026-01-01",
        }
        database.save_brain_concept(concept, "user-a")
        concept_query, concept_params = cursor.statements[1]
        self.assertIn("owner_id", concept_query)
        self.assertEqual(concept_params["owner_id"], "user-a")
        self.assertIn("concepts.owner_id IS NOT DISTINCT FROM EXCLUDED.owner_id", concept_query)

        link = {
            "id": "link-a", "from_concept_id": "concept-a", "to_concept_id": "concept-b",
            "relation": "related", "weight": 1, "created_at": "2026-01-01",
        }
        database.save_brain_concept_link(link, "user-a")
        link_query, link_params = cursor.statements[2]
        self.assertIn("source.owner_id=%(owner_id)s AND target.owner_id=%(owner_id)s", link_query)
        self.assertEqual(link_params["owner_id"], "user-a")

    def test_language_card_create_due_and_review_scope_by_owner(self):
        card = {
            "id": "card-a", "front": "hello", "back": "greeting",
            "language": "en", "source_note": None,
        }
        cursor = RecordingCursor(one_results=[{"id": "card-a"}])
        database = database_with_cursor(cursor)
        self.assertEqual(database.create_language_card(card, "user-a"), {"id": "card-a"})
        insert_query, insert_params = cursor.statements[0]
        self.assertIn("source_note,owner_id", insert_query)
        self.assertEqual(insert_params["owner_id"], "user-a")

        due_cursor = RecordingCursor()
        due_database = database_with_cursor(due_cursor)
        self.assertEqual(due_database.list_language_cards_due_for_owner("user-b", 10), [])
        due_query, due_params = due_cursor.statements[0]
        self.assertIn("WHERE owner_id=%s AND due_at<=now()", due_query)
        self.assertEqual(due_params, ("user-b", 10))

        card_row = {
            **card, "stability": 0, "difficulty": 5, "reps": 0, "lapses": 0,
        }
        update_row = {"id": "card-a"}
        review_cursor = RecordingCursor(one_results=[card_row, update_row])
        review_database = database_with_cursor(review_cursor)
        schedule = lambda _card, _rating: (1.0, 5.0, 1, 0, "learning", "due-date")
        self.assertEqual(
            review_database.review_language_card("card-a", "user-a", 4, schedule),
            update_row,
        )
        select_query, select_params = review_cursor.statements[0]
        update_query, update_params = review_cursor.statements[1]
        self.assertIn("id=%s AND owner_id=%s FOR UPDATE", select_query)
        self.assertEqual(select_params, ("card-a", "user-a"))
        self.assertIn("WHERE id=%s AND owner_id=%s", update_query)
        self.assertEqual(update_params[-2:], ("card-a", "user-a"))

    def test_vault_item_persistence_and_owner_scope(self):
        cursor = RecordingCursor(one_results=[{"id": "item-a"}])
        database = database_with_cursor(cursor)
        item = {"id": "item-a", "label": "Label", "ciphertext": "c", "nonce": "n", "kdf_salt": "s", "kdf_params": {}}
        database.save_vault_item(item, "user-a")
        insert_query, insert_params = cursor.statements[0]
        self.assertIn("owner_id", insert_query)
        self.assertEqual(insert_params["owner_id"], "user-a")

        get_cursor = RecordingCursor()
        get_db = database_with_cursor(get_cursor)
        self.assertIsNone(get_db.get_vault_item_for_owner("item-a", "user-b"))
        get_query, get_params = get_cursor.statements[0]
        self.assertIn("id=%s AND owner_id=%s", get_query)
        self.assertEqual(get_params, ("item-a", "user-b"))

        list_cursor = RecordingCursor()
        list_db = database_with_cursor(list_cursor)
        self.assertEqual(list_db.list_vault_items_for_owner("user-b"), [])
        list_query, list_params = list_cursor.statements[0]
        self.assertIn("WHERE owner_id=%s", list_query)
        self.assertEqual(list_params, ("user-b",))


if __name__ == "__main__":
    unittest.main()
