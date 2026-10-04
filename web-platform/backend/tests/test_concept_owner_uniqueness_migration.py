from pathlib import Path
import unittest


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "023_concepts_owner_unique.sql"
)


class ConceptOwnerUniquenessMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_discovers_exact_global_name_uniqueness_from_catalog(self):
        self.assertIn("from pg_index i", self.sql)
        self.assertIn("left join pg_constraint", self.sql)
        self.assertIn("i.indnkeyatts = 1", self.sql)
        self.assertIn("i.indkey[0] = name_attnum", self.sql)
        self.assertIn("i.indexprs is null", self.sql)
        self.assertIn("i.indpred is null", self.sql)
        self.assertIn("format('alter table public.concepts drop constraint %i'", self.sql)
        self.assertIn("format(\n        'drop index %i.%i'", self.sql)
        self.assertIn("another unique index involving name", self.sql)
        self.assertNotIn("drop constraint if exists concepts_name_key", self.sql)

    def test_rejects_ambiguous_global_uniqueness_definitions(self):
        self.assertIn("is a primary key", self.sql)
        self.assertIn("non-default uniqueness semantics", self.sql)
        self.assertIn("is backing constraint", self.sql)
        self.assertIn("exists with an unexpected definition", self.sql)

    def test_reports_existing_owner_name_collisions_before_index_creation(self):
        self.assertIn("group by owner_id, lower(name)", self.sql)
        self.assertIn("having count(*) > 1", self.sql)
        self.assertIn("where owner_id is not null", self.sql)
        self.assertIn("normalized name %, concept ids % collide", self.sql)
        self.assertLess(
            self.sql.index("cannot create owner-scoped concept uniqueness: owner_id"),
            self.sql.index("create unique index if not exists uq_concepts_owner_name"),
        )

    def test_owner_unique_index_preserves_unassigned_legacy_rows(self):
        self.assertIn(
            "on public.concepts(owner_id, lower(name))\n  where owner_id is not null",
            self.sql,
        )
        self.assertNotRegex(self.sql, r"\b(update|delete)\s+public\.concepts\b")


if __name__ == "__main__":
    unittest.main()
