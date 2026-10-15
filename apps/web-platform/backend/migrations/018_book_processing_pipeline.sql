ALTER TABLE public.books
  ADD COLUMN IF NOT EXISTS original_filename TEXT,
  ADD COLUMN IF NOT EXISTS processing_stage TEXT NOT NULL DEFAULT 'queued',
  ADD COLUMN IF NOT EXISTS processing_attempts INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS processing_error TEXT,
  ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS uq_books_content_hash
  ON public.books(content_hash)
  WHERE content_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_books_processing_queue
  ON public.books(status, created_at)
  WHERE status IN ('queued', 'processing', 'failed');
