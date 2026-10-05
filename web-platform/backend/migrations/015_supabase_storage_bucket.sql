-- Supabase Storage bucket for derived Cognix artifacts.
-- Keep private: backend access uses the service-role key only.
-- Supabase already provides this schema/table; the IF NOT EXISTS bootstrap keeps
-- local PostgreSQL CI/integration databases compatible without mutating an
-- existing Supabase Storage implementation.
CREATE SCHEMA IF NOT EXISTS storage;
CREATE TABLE IF NOT EXISTS storage.buckets (
  id text primary key,
  name text not null,
  public boolean not null default false
);

INSERT INTO storage.buckets (id, name, public)
VALUES ('cognix-artifacts', 'cognix-artifacts', false)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    public = false;
