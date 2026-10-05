from pathlib import Path
import unittest


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "025_rls_owner_isolation.sql"
)


class RlsOwnerIsolationMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_owner_tables_use_jwt_subject_and_fail_closed_for_legacy_rows(self):
        for table in (
            "sources",
            "books",
            "notes",
            "concepts",
            "language_cards",
            "vault_items",
        ):
            self.assertIn(
                f"create policy cognix_authenticated_{table}",
                self.sql,
            )
            self.assertIn(
                "owner_id is not null and owner_id = current_setting('request.jwt.claim.sub', true)",
                self.sql,
            )

    def test_relationship_tables_are_scoped_through_owned_parents(self):
        for table in (
            "processing_tasks",
            "claims",
            "reviews",
            "export_jobs",
            "chapters",
            "chunks",
            "book_summaries",
            "summary_sources",
            "note_sources",
            "concept_links",
            "language_reviews",
        ):
            self.assertIn(f"create policy cognix_authenticated_{table}", self.sql)

    def test_api_roles_are_deny_by_default(self):
        self.assertIn("create policy cognix_anon_deny", self.sql)
        self.assertIn("using (false) with check (false)", self.sql)
        self.assertIn("create policy cognix_authenticated_deny", self.sql)

    def test_migration_has_no_data_backfill(self):
        self.assertNotRegex(self.sql, r"\b(update|delete|truncate)\s+public\.")

if __name__ == "__main__":
    unittest.main()
