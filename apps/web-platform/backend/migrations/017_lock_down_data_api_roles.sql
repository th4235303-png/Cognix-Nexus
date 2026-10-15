-- Security hardening: the application accesses Postgres directly through FastAPI/worker.
-- Supabase Data API roles must not retain table/sequence privileges when RLS
-- is intentionally policy-less. Keep service_role for server-side administration.
-- Supabase already provides these roles; create them only for local PostgreSQL
-- integration databases so the same migration ledger remains portable.
do $migration$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
end
$migration$;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM PUBLIC, anon, authenticated;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC, anon, authenticated;
