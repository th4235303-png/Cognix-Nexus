-- Phase 7-12 hardening: reviewable knowledge, resumable AI backoff and provider audit.
ALTER TABLE public.knowledge_items
  ADD COLUMN IF NOT EXISTS review_note TEXT,
  ADD COLUMN IF NOT EXISTS reviewed_by TEXT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS canonical_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS dedupe_key TEXT;

CREATE INDEX IF NOT EXISTS idx_knowledge_items_owner_status
  ON public.knowledge_items(owner_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_owner_dedupe
  ON public.knowledge_items(owner_id, dedupe_key)
  WHERE dedupe_key IS NOT NULL;

ALTER TABLE public.book_reading_progress
  ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_error_type TEXT;

CREATE INDEX IF NOT EXISTS idx_book_reading_progress_due
  ON public.book_reading_progress(status, next_attempt_at, updated_at);

CREATE TABLE IF NOT EXISTS public.ai_provider_events (
  id TEXT PRIMARY KEY,
  owner_id TEXT,
  book_id TEXT REFERENCES public.books(id) ON DELETE SET NULL,
  stage TEXT NOT NULL,
  provider_url TEXT,
  model TEXT,
  status TEXT NOT NULL,
  latency_ms NUMERIC(12,2),
  error_type TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_provider_events_owner_time
  ON public.ai_provider_events(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_provider_events_book_time
  ON public.ai_provider_events(book_id, created_at DESC);

ALTER TABLE public.ai_provider_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cognix_anon_deny ON public.ai_provider_events;
CREATE POLICY cognix_anon_deny ON public.ai_provider_events
  FOR ALL TO anon USING (false) WITH CHECK (false);
DROP POLICY IF EXISTS cognix_authenticated_owner ON public.ai_provider_events;
CREATE POLICY cognix_authenticated_owner ON public.ai_provider_events
  FOR ALL TO authenticated
  USING (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true))
  WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting('request.jwt.claim.sub', true));

-- Canonical promotion is explicit; AI-generated knowledge stays draft until reviewed.
