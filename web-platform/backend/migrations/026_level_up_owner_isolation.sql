-- Phase 7: Level-Up / learning ownership isolation.
-- Legacy rows remain ownerless and therefore inaccessible to authenticated users until
-- an explicit, audited ownership mapping exists. No data is deleted or reassigned.

DO $$
DECLARE
  t text;
  tables text[] := ARRAY[
    'feynman_reviews','learning_reviews','interleaving_sets','learning_paths',
    'knowledge_gaps','syntheses','decisions','writing_drafts','research_reports',
    'research_claims','life_events','context_snapshots','wiki_pages',
    'growth_snapshots','ideas','sync_conflicts','sync_revisions',
    'legacy_manifests','agent_schedules','agent_jobs','job_leases','backup_manifests'
  ];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format('ALTER TABLE public.%I ADD COLUMN IF NOT EXISTS owner_id text', t);
    EXECUTE format('ALTER TABLE public.%I ALTER COLUMN owner_id SET DEFAULT NULLIF(current_setting(''request.jwt.claim.sub'', true), '''')', t);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON public.%I(owner_id)', 'idx_'||t||'_owner_id', t);
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS cognix_anon_deny_'||t||' ON public.%I', t);
    EXECUTE format(
      'CREATE POLICY cognix_anon_deny_%s ON public.%I FOR ALL TO anon USING (false) WITH CHECK (false)',
      t, t
    );
    EXECUTE format('DROP POLICY IF EXISTS cognix_authenticated_%s ON public.%I', t, t);
    EXECUTE format(
      'CREATE POLICY cognix_authenticated_%s ON public.%I FOR ALL TO authenticated
       USING (owner_id IS NOT NULL AND owner_id = current_setting(''request.jwt.claim.sub'', true))
       WITH CHECK (owner_id IS NOT NULL AND owner_id = current_setting(''request.jwt.claim.sub'', true))',
      t, t
    );
  END LOOP;
END $$;
