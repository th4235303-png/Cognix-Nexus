ALTER TABLE public.processing_tasks
  ADD COLUMN IF NOT EXISTS claimed_by TEXT,
  ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_processing_tasks_claimed_at
  ON public.processing_tasks(claimed_at)
  WHERE claimed_at IS NOT NULL;
