-- Defense-in-depth RLS for the direct-Postgres application model.
-- The backend/worker use a privileged PostgreSQL role and therefore bypass RLS.
-- Supabase Data API roles remain deny-by-default; authenticated access is allowed
-- only where the row can be tied to the caller's JWT subject.
--
-- Do not backfill legacy NULL owner_id rows. They remain inaccessible to
-- authenticated Data API callers.

DO $migration$
DECLARE
  table_name TEXT;
  protected_tables CONSTANT TEXT[] := ARRAY[
    'sources','books','notes','concepts','language_cards','vault_items',
    'processing_tasks','claims','reviews','export_jobs',
    'chapters','chunks','book_summaries','summary_sources',
    'note_sources','concept_links','language_reviews'
  ];
BEGIN
  FOREACH table_name IN ARRAY protected_tables
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS cognix_anon_deny ON public.%I', table_name);
    EXECUTE format(
      'CREATE POLICY cognix_anon_deny ON public.%I FOR ALL TO anon USING (false) WITH CHECK (false)',
      table_name
    );
  END LOOP;
END
$migration$;

DROP POLICY IF EXISTS cognix_authenticated_sources ON public.sources;
CREATE POLICY cognix_authenticated_sources
  ON public.sources FOR ALL TO authenticated
  USING (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true))
  WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS cognix_authenticated_books ON public.books;
CREATE POLICY cognix_authenticated_books
  ON public.books FOR ALL TO authenticated
  USING (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true))
  WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS cognix_authenticated_notes ON public.notes;
CREATE POLICY cognix_authenticated_notes
  ON public.notes FOR ALL TO authenticated
  USING (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true))
  WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS cognix_authenticated_concepts ON public.concepts;
CREATE POLICY cognix_authenticated_concepts
  ON public.concepts FOR ALL TO authenticated
  USING (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true))
  WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS cognix_authenticated_language_cards ON public.language_cards;
CREATE POLICY cognix_authenticated_language_cards
  ON public.language_cards FOR ALL TO authenticated
  USING (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true))
  WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS cognix_authenticated_vault_items ON public.vault_items;
CREATE POLICY cognix_authenticated_vault_items
  ON public.vault_items FOR ALL TO authenticated
  USING (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true))
  WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS cognix_authenticated_processing_tasks ON public.processing_tasks;
CREATE POLICY cognix_authenticated_processing_tasks
  ON public.processing_tasks FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = processing_tasks.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = processing_tasks.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_claims ON public.claims;
CREATE POLICY cognix_authenticated_claims
  ON public.claims FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = claims.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = claims.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_reviews ON public.reviews;
CREATE POLICY cognix_authenticated_reviews
  ON public.reviews FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = reviews.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = reviews.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_export_jobs ON public.export_jobs;
CREATE POLICY cognix_authenticated_export_jobs
  ON public.export_jobs FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = export_jobs.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sources s
      WHERE s.id = export_jobs.source_id
        AND s.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_chapters ON public.chapters;
CREATE POLICY cognix_authenticated_chapters
  ON public.chapters FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.books b
      WHERE b.id = chapters.book_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.books b
      WHERE b.id = chapters.book_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_chunks ON public.chunks;
CREATE POLICY cognix_authenticated_chunks
  ON public.chunks FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM public.chapters ch
      JOIN public.books b ON b.id = ch.book_id
      WHERE ch.id = chunks.chapter_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM public.chapters ch
      JOIN public.books b ON b.id = ch.book_id
      WHERE ch.id = chunks.chapter_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_book_summaries ON public.book_summaries;
CREATE POLICY cognix_authenticated_book_summaries
  ON public.book_summaries FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.books b
      WHERE b.id = book_summaries.book_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.books b
      WHERE b.id = book_summaries.book_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_summary_sources ON public.summary_sources;
CREATE POLICY cognix_authenticated_summary_sources
  ON public.summary_sources FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM public.book_summaries bs
      JOIN public.books b ON b.id = bs.book_id
      WHERE bs.id = summary_sources.summary_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM public.book_summaries bs
      JOIN public.books b ON b.id = bs.book_id
      WHERE bs.id = summary_sources.summary_id
        AND b.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_note_sources ON public.note_sources;
CREATE POLICY cognix_authenticated_note_sources
  ON public.note_sources FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.notes n
      WHERE n.id = note_sources.note_id
        AND n.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.notes n
      WHERE n.id = note_sources.note_id
        AND n.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_concept_links ON public.concept_links;
CREATE POLICY cognix_authenticated_concept_links
  ON public.concept_links FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM public.concepts c1
      JOIN public.concepts c2 ON c2.id = concept_links.to_concept_id
      WHERE c1.id = concept_links.from_concept_id
        AND c1.owner_id = current_setting('request.jwt.claim.sub', true)
        AND c2.owner_id = c1.owner_id
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM public.concepts c1
      JOIN public.concepts c2 ON c2.id = concept_links.to_concept_id
      WHERE c1.id = concept_links.from_concept_id
        AND c1.owner_id = current_setting('request.jwt.claim.sub', true)
        AND c2.owner_id = c1.owner_id
    )
  );

DROP POLICY IF EXISTS cognix_authenticated_language_reviews ON public.language_reviews;
CREATE POLICY cognix_authenticated_language_reviews
  ON public.language_reviews FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.language_cards lc
      WHERE lc.id = language_reviews.card_id
        AND lc.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.language_cards lc
      WHERE lc.id = language_reviews.card_id
        AND lc.owner_id = current_setting('request.jwt.claim.sub', true)
    )
  );

-- Every other public table stays explicitly deny-by-default for both API roles.
-- This keeps future accidental grants from exposing rows before an intentional
-- policy is added for that table.
DO $migration$
DECLARE
  table_name TEXT;
  protected_tables CONSTANT TEXT[] := ARRAY[
    'sources','books','notes','concepts','language_cards','vault_items',
    'processing_tasks','claims','reviews','export_jobs',
    'chapters','chunks','book_summaries','summary_sources',
    'note_sources','concept_links','language_reviews'
  ];
BEGIN
  FOR table_name IN
    SELECT c.relname
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname='public' AND c.relkind='r'
      AND NOT (c.relname = ANY(protected_tables))
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS cognix_anon_deny ON public.%I', table_name);
    EXECUTE format(
      'CREATE POLICY cognix_anon_deny ON public.%I FOR ALL TO anon USING (false) WITH CHECK (false)',
      table_name
    );
    EXECUTE format('DROP POLICY IF EXISTS cognix_authenticated_deny ON public.%I', table_name);
    EXECUTE format(
      'CREATE POLICY cognix_authenticated_deny ON public.%I FOR ALL TO authenticated USING (false) WITH CHECK (false)',
      table_name
    );
  END LOOP;
END
$migration$;
