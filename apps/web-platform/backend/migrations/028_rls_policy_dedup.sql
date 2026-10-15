-- Remove redundant deny policies introduced by the level-up owner-isolation migration.
-- Owner-scoped authenticated policies remain the positive authorization path.
-- RLS with no matching anon policy is deny-by-default, so removing the
-- level-up-specific anon deny policies does not open access.
DO $migration$
DECLARE
  table_name TEXT;
  protected_tables CONSTANT TEXT[] := ARRAY[
    'feynman_reviews','learning_reviews','interleaving_sets','learning_paths',
    'knowledge_gaps','syntheses','decisions','writing_drafts',
    'research_reports','research_claims','life_events','context_snapshots',
    'wiki_pages','growth_snapshots','ideas','sync_conflicts',
    'sync_revisions','legacy_manifests','agent_schedules','agent_jobs',
    'job_leases','backup_manifests'
  ];
BEGIN
  FOREACH table_name IN ARRAY protected_tables
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS cognix_anon_deny_%s ON public.%I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS cognix_authenticated_deny ON public.%I', table_name);
  END LOOP;
END
$migration$;
