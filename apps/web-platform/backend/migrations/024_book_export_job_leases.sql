ALTER TABLE public.books
  ADD COLUMN IF NOT EXISTS processing_claimed_by TEXT,
  ADD COLUMN IF NOT EXISTS processing_claimed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS processing_claim_token TEXT;

ALTER TABLE public.export_jobs
  ADD COLUMN IF NOT EXISTS claimed_by TEXT,
  ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS claim_token TEXT;

DO $migration$
DECLARE
  expected_column RECORD;
  actual_column RECORD;
BEGIN
  FOR expected_column IN
    SELECT *
    FROM (VALUES
      ('books', 'processing_claimed_by', 'text'),
      ('books', 'processing_claimed_at', 'timestamp with time zone'),
      ('books', 'processing_claim_token', 'text'),
      ('export_jobs', 'claimed_by', 'text'),
      ('export_jobs', 'claimed_at', 'timestamp with time zone'),
      ('export_jobs', 'claim_token', 'text')
    ) AS expected(table_name, column_name, data_type)
  LOOP
    SELECT format_type(attribute.atttypid, attribute.atttypmod) AS data_type,
           attribute.attnotnull,
           attribute.atthasdef
    INTO actual_column
    FROM pg_attribute attribute
    WHERE attribute.attrelid = to_regclass('public.' || expected_column.table_name)
      AND attribute.attname = expected_column.column_name
      AND NOT attribute.attisdropped;

    IF NOT FOUND THEN
      RAISE EXCEPTION
        'Cannot apply job lease migration: public.%.% is missing',
        expected_column.table_name,
        expected_column.column_name;
    END IF;

    IF actual_column.data_type <> expected_column.data_type
       OR actual_column.attnotnull
       OR actual_column.atthasdef THEN
      RAISE EXCEPTION
        'Cannot apply job lease migration: public.%.% must be nullable % without a default',
        expected_column.table_name,
        expected_column.column_name,
        expected_column.data_type;
    END IF;
  END LOOP;
END
$migration$;
