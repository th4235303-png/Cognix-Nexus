-- Persist client idempotency keys for mobile/offline note creation retries.
ALTER TABLE public.notes ADD COLUMN IF NOT EXISTS idempotency_key text;
CREATE UNIQUE INDEX IF NOT EXISTS idx_notes_owner_idempotency_key
  ON public.notes(owner_id, idempotency_key)
  WHERE owner_id IS NOT NULL AND idempotency_key IS NOT NULL;
