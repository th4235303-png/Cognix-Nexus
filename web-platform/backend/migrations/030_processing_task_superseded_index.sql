-- Cover the superseded_by foreign key for latest-action cancellation lookups.
CREATE INDEX IF NOT EXISTS idx_processing_tasks_superseded_by
  ON public.processing_tasks(superseded_by)
  WHERE superseded_by IS NOT NULL;
