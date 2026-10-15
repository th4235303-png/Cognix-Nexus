-- Supabase advisor follow-up: avoid per-row JWT setting evaluation and cover the knowledge_items chapter FK.
-- Keep the same owner comparison and deny-by-default anonymous policies; this changes evaluation cost, not access semantics.

CREATE INDEX IF NOT EXISTS idx_knowledge_items_chapter_id
  ON public.knowledge_items(chapter_id);

DO $migration$
DECLARE
  table_name TEXT;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'book_reading_progress',
    'reading_events',
    'chapter_summaries',
    'knowledge_items',
    'lesson_packs',
    'derived_books',
    'ai_provider_events'
  ]
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS cognix_authenticated_owner ON public.%I', table_name);
    EXECUTE format(
      'CREATE POLICY cognix_authenticated_owner ON public.%I
       FOR ALL TO authenticated
       USING (owner_id IS NOT NULL AND owner_id = (SELECT current_setting(''request.jwt.claim.sub'', true)))
       WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting(''request.jwt.claim.sub'', true)))',
      table_name
    );
  END LOOP;
END
$migration$;
