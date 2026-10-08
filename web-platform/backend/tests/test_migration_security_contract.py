from __future__ import annotations

from pathlib import Path
import re
import unittest


BACKEND = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND / "migrations"


class MigrationSecurityContractTests(unittest.TestCase):
    def test_020_to_027_are_registered_once_in_order_and_required(self):
        persistence = (BACKEND / "app" / "persistence.py").read_text(encoding="utf-8").lower()
        start = persistence.index("migration_names = (")
        end = persistence.index(")\n        with self.connect", start)
        registered = re.findall(r'"(\d{3}_[^"]+\.sql)"', persistence[start:end])
        expected = [
            "020_record_ownership.sql",
            "021_brain_record_ownership.sql",
            "022_vault_item_ownership.sql",
            "023_concepts_owner_unique.sql",
            "024_book_export_job_leases.sql",
            "025_rls_owner_isolation.sql",
            "026_level_up_owner_isolation.sql",
            "027_rls_helper_performance.sql",
            "028_rls_policy_dedup.sql",
        ]
        tail = registered[-len(expected):]
        self.assertEqual(tail, expected)
        for migration_name in expected:
            self.assertEqual(registered.count(migration_name), 1)
            self.assertTrue((MIGRATIONS / migration_name).is_file())
        self.assertLess(
            registered.index("017_lock_down_data_api_roles.sql"),
            registered.index("018_book_processing_pipeline.sql"),
        )
        self.assertNotIn("migration.exists()", persistence)
        self.assertIn("pg_advisory_xact_lock", persistence)
        self.assertIn("incomplete base schema", persistence)
        self.assertIn("cognix_schema_migrations", persistence)
        self.assertIn("on conflict (migration_name) do nothing", persistence)
        self.assertIn("if migration_name in applied", persistence)

    def test_020_to_022_only_add_nullable_owner_columns_and_indexes(self):
        expectations = {
            "020_record_ownership.sql": ("sources", "books"),
            "021_brain_record_ownership.sql": ("notes", "concepts", "language_cards"),
            "022_vault_item_ownership.sql": ("vault_items",),
        }
        for migration_name, tables in expectations.items():
            with self.subTest(migration=migration_name):
                sql = (MIGRATIONS / migration_name).read_text(encoding="utf-8").lower()
                self.assertNotRegex(sql, r"\b(update|delete|truncate|drop)\b")
                self.assertEqual(sql.count("add column if not exists owner_id text"), len(tables))
                self.assertNotRegex(sql, r"owner_id\s+text\s+not null")
                self.assertIn("attribute.attnotnull", sql)
                self.assertIn("attribute.atthasdef", sql)
                self.assertIn("must be nullable text without a default", sql)

    def test_023_only_removes_catalog_verified_name_only_uniqueness(self):
        sql = (MIGRATIONS / "023_concepts_owner_unique.sql").read_text(encoding="utf-8").lower()
        self.assertIn("from pg_index i", sql)
        self.assertIn("i.indnkeyatts = 1", sql)
        self.assertIn("i.indkey[0] = name_attnum", sql)
        self.assertIn("i.indexprs is null", sql)
        self.assertIn("i.indpred is null", sql)
        self.assertIn("uniqueness.indnatts <> 1", sql)
        self.assertIn("includes additional columns", sql)
        self.assertIn("uniqueness.contype = 'p'", sql)
        self.assertIn("uniqueness.contype <> 'u'", sql)
        self.assertIn("group by owner_id, lower(name)", sql)
        self.assertIn("where owner_id is not null", sql)
        self.assertIn("having count(*) > 1", sql)
        self.assertLess(
            sql.index("normalized name %, concept ids % collide"),
            sql.index("create unique index if not exists uq_concepts_owner_name"),
        )
        self.assertNotRegex(sql, r"\b(update|delete|truncate)\s+public\.concepts\b")

    def test_024_targets_job_tables_with_nullable_default_free_lease_columns(self):
        sql = (MIGRATIONS / "024_book_export_job_leases.sql").read_text(encoding="utf-8").lower()
        self.assertIn("alter table public.books", sql)
        self.assertIn("alter table public.export_jobs", sql)
        self.assertNotIn("alter table public.processing_tasks", sql)
        for column in (
            "processing_claimed_by text",
            "processing_claimed_at timestamptz",
            "processing_claim_token text",
            "claimed_by text",
            "claimed_at timestamptz",
            "claim_token text",
        ):
            with self.subTest(column=column):
                self.assertIn(column, sql)
        self.assertIn("attribute.attnotnull", sql)
        self.assertIn("attribute.atthasdef", sql)
        self.assertIn("must be nullable", sql)
        self.assertNotRegex(sql, r"\b(update|delete|truncate|drop)\b")

    def test_027_wraps_owner_claim_lookup_in_scalar_subqueries(self):
        sql = (MIGRATIONS / "027_rls_helper_performance.sql").read_text(encoding="utf-8").lower()
        self.assertIn("pg_policy", sql)
        self.assertIn("alter policy", sql)
        self.assertIn("(select current_setting(''request.jwt.claim.sub'', true))", sql)
        self.assertNotIn("drop policy", sql)

    def test_backend_only_privilege_model_revokes_public_and_data_api_roles(self):
        migration_paths = sorted(MIGRATIONS.glob("*.sql"))
        sql = "\n".join(path.read_text(encoding="utf-8").lower() for path in migration_paths)
        self.assertNotRegex(sql, r"\bgrant\s+")
        self.assertIn(
            "revoke all privileges on all tables in schema public from public, anon, authenticated",
            sql,
        )
        self.assertIn(
            "revoke all privileges on all sequences in schema public from public, anon, authenticated",
            sql,
        )
        self.assertNotRegex(sql, r"grant\s+")
        rls_sql = (MIGRATIONS / "025_rls_owner_isolation.sql").read_text(encoding="utf-8").lower()
        self.assertIn("alter table public.sources enable row level security", rls_sql)
        self.assertIn("create policy cognix_authenticated_sources", rls_sql)
        self.assertIn("current_setting('request.jwt.claim.sub', true)", rls_sql)
        self.assertIn("using (false) with check (false)", rls_sql)
        self.assertIn("owner_id is not null", rls_sql)

    def test_authenticated_owner_paths_match_parent_owner_and_leave_null_owners_out(self):
        persistence = (BACKEND / "app" / "persistence.py").read_text(encoding="utf-8").lower()
        ownership = (BACKEND / "app" / "ownership.py").read_text(encoding="utf-8").lower()
        for predicate in (
            "where id=%s and owner_id=%s",
            "where b.id=%s and b.owner_id=%s",
            "where t.id=%s and s.owner_id=%s",
            "where owner_id=%s and lower(name)=lower(%s)",
            "where source.owner_id=%s and target.owner_id=%s",
            "where id=%s and owner_id=%s for update",
            "where owner_id=%s order by updated_at desc",
        ):
            with self.subTest(predicate=predicate):
                self.assertIn(predicate, persistence)
        self.assertIn("where parent.id=%s and parent.owner_id=%s", persistence)
        self.assertIn("source.owner_id=%(owner_id)s and target.owner_id=%(owner_id)s", persistence)
        self.assertIn('if subject == "anonymous":', ownership)
        self.assertIn("cognix_dev_mode", ownership)
        self.assertIn("raise httpexception(status_code=401", ownership)


if __name__ == "__main__":
    unittest.main()
