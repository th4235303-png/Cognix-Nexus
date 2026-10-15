-- Prevent concurrent API requests from creating duplicate active processing tasks.
CREATE UNIQUE INDEX IF NOT EXISTS uq_processing_active_source
  ON public.processing_tasks(source_id)
  WHERE status IN ('queued', 'running');
