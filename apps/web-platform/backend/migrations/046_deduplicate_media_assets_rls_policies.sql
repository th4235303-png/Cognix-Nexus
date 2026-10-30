-- Remove redundant permissive deny policies on media_assets.
-- The retained anon deny policy remains default-deny for anon.
-- Authenticated access continues to be limited by cognix_authenticated_owner.
DROP POLICY IF EXISTS cognix_deny_anonymous ON public.media_assets;
DROP POLICY IF EXISTS cognix_authenticated_deny ON public.media_assets;
