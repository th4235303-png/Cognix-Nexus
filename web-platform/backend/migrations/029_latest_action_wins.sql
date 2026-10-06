-- Latest-action-wins processing semantics.
-- A cancelled task is a durable audit record and is never runnable again.
ALTER TABLE public.processing_tasks
  DROP CONSTRAINT IF EXISTS processing_tasks_status_check;

ALTER TABLE public.processing_tasks
  ADD COLUMN IF NOT EXISTS idempotency_key TEXT,
  ADD COLUMN IF NOT EXISTS superseded_by TEXT REFERENCES public.processing_tasks(id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_processing_task_idempotency_key
  ON public.processing_tasks(idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_processing_tasks_runnable_latest
  ON public.processing_tasks(source_id, status, updated_at DESC);
