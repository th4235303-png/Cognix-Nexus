-- Restrict service-managed Brain Soul and YouTube tracker tables to backend/service-role access.
-- These tables have RLS enabled but intentionally have no user-facing policies.
-- Remove default Supabase Data API grants that can be re-added to newly-created tables.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  REVOKE ALL ON SEQUENCES FROM anon, authenticated;

REVOKE ALL PRIVILEGES ON TABLE
  public.brain_soul_context,
  public.brain_soul_syntheses,
  public.youtube_channels,
  public.brain_youtube_videos
FROM anon, authenticated;

REVOKE ALL PRIVILEGES ON SEQUENCE
  public.brain_soul_context_id_seq,
  public.brain_soul_syntheses_id_seq,
  public.youtube_channels_id_seq,
  public.brain_youtube_videos_id_seq
FROM anon, authenticated;
