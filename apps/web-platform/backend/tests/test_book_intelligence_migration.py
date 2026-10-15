from pathlib import Path


def test_book_intelligence_migration_contract():
    path = Path(__file__).parents[1] / "migrations" / "031_book_intelligence.sql"
    sql = path.read_text(encoding="utf-8")
    for name in (
        "book_reading_progress",
        "reading_events",
        "chapter_summaries",
        "knowledge_items",
        "lesson_packs",
        "derived_books",
    ):
        assert "CREATE TABLE IF NOT EXISTS public." + name in sql
    assert "uq_books_owner_content_hash" in sql
    assert "ALTER TABLE public.books" in sql
    assert "owner_id" in sql
