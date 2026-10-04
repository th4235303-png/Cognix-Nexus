ALTER TABLE public.vault_items
  ADD COLUMN IF NOT EXISTS owner_id TEXT;

CREATE INDEX IF NOT EXISTS idx_vault_items_owner_updated_at
  ON public.vault_items(owner_id, updated_at DESC);

DO $migration$
DECLARE
  actual_column RECORD;
BEGIN
  SELECT format_type(attribute.atttypid, attribute.atttypmod) AS data_type,
         attribute.attnotnull,
         attribute.atthasdef
  INTO actual_column
  FROM pg_attribute attribute
  WHERE attribute.attrelid = 'public.vault_items'::regclass
    AND attribute.attname = 'owner_id'
    AND NOT attribute.attisdropped;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Cannot apply ownership migration: public.vault_items.owner_id is missing';
  END IF;

  IF actual_column.data_type <> 'text'
     OR actual_column.attnotnull
     OR actual_column.atthasdef THEN
    RAISE EXCEPTION
      'Cannot apply ownership migration: public.vault_items.owner_id must be nullable text without a default';
  END IF;
END
$migration$;
