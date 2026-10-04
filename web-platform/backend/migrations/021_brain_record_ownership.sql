ALTER TABLE public.notes
  ADD COLUMN IF NOT EXISTS owner_id TEXT;

ALTER TABLE public.concepts
  ADD COLUMN IF NOT EXISTS owner_id TEXT;

ALTER TABLE public.language_cards
  ADD COLUMN IF NOT EXISTS owner_id TEXT;

CREATE INDEX IF NOT EXISTS idx_concepts_owner_name
  ON public.concepts(owner_id, lower(name))
  WHERE owner_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_notes_owner_updated_at
  ON public.notes(owner_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_language_cards_owner_due_at
  ON public.language_cards(owner_id, due_at);

DO $migration$
DECLARE
  table_name TEXT;
  actual_column RECORD;
BEGIN
  FOREACH table_name IN ARRAY ARRAY['notes', 'concepts', 'language_cards']
  LOOP
    SELECT format_type(attribute.atttypid, attribute.atttypmod) AS data_type,
           attribute.attnotnull,
           attribute.atthasdef
    INTO actual_column
    FROM pg_attribute attribute
    WHERE attribute.attrelid = to_regclass('public.' || table_name)
      AND attribute.attname = 'owner_id'
      AND NOT attribute.attisdropped;

    IF NOT FOUND THEN
      RAISE EXCEPTION 'Cannot apply ownership migration: public.%.owner_id is missing', table_name;
    END IF;

    IF actual_column.data_type <> 'text'
       OR actual_column.attnotnull
       OR actual_column.atthasdef THEN
      RAISE EXCEPTION
        'Cannot apply ownership migration: public.%.owner_id must be nullable text without a default',
        table_name;
    END IF;
  END LOOP;
END
$migration$;
