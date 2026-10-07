-- Book Intelligence: durable background reading, checkpoints, distilled knowledge and synthesis.
ALTER TABLE public.books
  ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT 'Unclassified',
  ADD COLUMN IF NOT EXISTS ai_reading_paused_reason TEXT;

DROP INDEX IF EXISTS public.uq_books_content_hash;
CREATE UNIQUE INDEX IF NOT EXISTS uq_books_owner_content_hash
  ON public.books(owner_id, content_hash)
  WHERE owner_id IS NOT NULL AND content_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.book_reading_progress (
  book_id TEXT PRIMARY KEY REFERENCES public.books(id) ON DELETE CASCADE,
  owner_id TEXT,
  stage TEXT NOT NULL DEFAULT 'queued',
  status TEXT NOT NULL DEFAULT 'queued',
  completed_units INTEGER NOT NULL DEFAULT 0,
  total_units INTEGER NOT NULL DEFAULT 0,
  percent NUMERIC(5,2) NOT NULL DEFAULT 0,
  current_chapter_id TEXT,
  current_chapter_number INTEGER,
  last_checkpoint_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  paused_reason TEXT,
  claim_token TEXT,
  claimed_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_book_reading_progress_owner ON public.book_reading_progress(owner_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.reading_events (
  id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES public.books(id) ON DELETE CASCADE,
  owner_id TEXT,
  event_type TEXT NOT NULL,
  stage TEXT NOT NULL,
  percent NUMERIC(5,2),
  chapter_id TEXT,
  chapter_number INTEGER,
  message TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reading_events_book_time ON public.reading_events(book_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.chapter_summaries (
  id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES public.books(id) ON DELETE CASCADE,
  chapter_id TEXT NOT NULL REFERENCES public.chapters(id) ON DELETE CASCADE,
  owner_id TEXT,
  status TEXT NOT NULL DEFAULT 'partial',
  content TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  model TEXT,
  source_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(chapter_id, version)
);
CREATE INDEX IF NOT EXISTS idx_chapter_summaries_book ON public.chapter_summaries(book_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.knowledge_items (
  id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES public.books(id) ON DELETE CASCADE,
  chapter_id TEXT REFERENCES public.chapters(id) ON DELETE SET NULL,
  owner_id TEXT,
  category TEXT NOT NULL DEFAULT 'Unclassified',
  knowledge_type TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  confidence NUMERIC(5,4),
  status TEXT NOT NULL DEFAULT 'draft',
  model TEXT,
  source_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_owner_category ON public.knowledge_items(owner_id, category, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_book ON public.knowledge_items(book_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.lesson_packs (
  id TEXT PRIMARY KEY,
  owner_id TEXT,
  title TEXT NOT NULL,
  category TEXT,
  topic TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  content TEXT NOT NULL,
  source_book_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_knowledge_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  model TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lesson_packs_owner ON public.lesson_packs(owner_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.derived_books (
  id TEXT PRIMARY KEY,
  owner_id TEXT,
  title TEXT NOT NULL,
  category TEXT,
  topic TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  content TEXT NOT NULL,
  source_book_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_knowledge_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  model TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_derived_books_owner ON public.derived_books(owner_id, updated_at DESC);

DO $migration$
DECLARE table_name TEXT;
BEGIN
  FOREACH table_name IN ARRAY ARRAY['book_reading_progress','reading_events','chapter_summaries','knowledge_items','lesson_packs','derived_books'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
    EXECUTE format('DROP POLICY IF EXISTS cognix_anon_deny ON public.%I', table_name);
    EXECUTE format('CREATE POLICY cognix_anon_deny ON public.%I FOR ALL TO anon USING (false) WITH CHECK (false)', table_name);
    EXECUTE format('DROP POLICY IF EXISTS cognix_authenticated_owner ON public.%I', table_name);
    EXECUTE format('CREATE POLICY cognix_authenticated_owner ON public.%I FOR ALL TO authenticated USING (owner_id IS NOT NULL AND owner_id = current_setting(''request.jwt.claim.sub'', true)) WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting(''request.jwt.claim.sub'', true))', table_name);
  END LOOP;
END
$migration$;