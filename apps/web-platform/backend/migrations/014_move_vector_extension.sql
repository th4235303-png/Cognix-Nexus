-- Keep the pgvector extension out of the public schema.
CREATE SCHEMA IF NOT EXISTS extensions;
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_extension e
    JOIN pg_namespace n ON n.oid = e.extnamespace
    WHERE e.extname = 'vector'
      AND n.nspname <> 'extensions'
  ) THEN
    EXECUTE 'ALTER EXTENSION vector SET SCHEMA extensions';
  END IF;
END
$$;
