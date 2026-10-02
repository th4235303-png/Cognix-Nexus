-- Security hardening: the application accesses Postgres directly through FastAPI/worker.
-- Supabase Data API roles must not retain table/sequence privileges when RLS
-- is intentionally policy-less. Keep service_role for server-side administration.
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
