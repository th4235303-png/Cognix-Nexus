-- Supabase Storage bucket for derived Cognix artifacts.
-- Keep private: backend access uses the service-role key only.
INSERT INTO storage.buckets (id, name, public)
VALUES ('cognix-artifacts', 'cognix-artifacts', false)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    public = false;
