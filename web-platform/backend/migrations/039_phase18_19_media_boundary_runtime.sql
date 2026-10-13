-- Phase 18/19: Media Boundary and Native Capabilities runtime
-- Migration 039
-- Tables: media_assets, media_ocr_results, media_device_gates
-- RLS: initplan-safe pattern (SELECT current_setting(...)) — never session-level

-- ─── media_assets ─────────────────────────────────────────────────────────────
-- Stores references to media files (storage URIs only — no raw bytes).

CREATE TABLE IF NOT EXISTS public.media_assets (
    id             TEXT        NOT NULL PRIMARY KEY,
    owner_id       TEXT        NOT NULL,
    storage_ref    TEXT        NOT NULL,
    content_sha256 TEXT        NOT NULL,
    source_ref     TEXT        NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS media_assets_owner_id_idx
    ON public.media_assets (owner_id);

CREATE INDEX IF NOT EXISTS media_assets_source_ref_idx
    ON public.media_assets (owner_id, source_ref);

ALTER TABLE public.media_assets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.media_assets;
CREATE POLICY cognix_authenticated_owner ON public.media_assets
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.media_assets;
CREATE POLICY cognix_deny_anonymous ON public.media_assets
    FOR ALL TO anon USING (false);


-- ─── media_ocr_results ────────────────────────────────────────────────────────
-- Stores OCR text results linked to a media asset (lineage via asset_id + source_ref).

CREATE TABLE IF NOT EXISTS public.media_ocr_results (
    id         TEXT        NOT NULL PRIMARY KEY,
    owner_id   TEXT        NOT NULL,
    asset_id   TEXT        NOT NULL,
    text       TEXT        NOT NULL DEFAULT '',
    source_ref TEXT        NOT NULL,
    provider   TEXT        NOT NULL,
    status     TEXT        NOT NULL DEFAULT 'draft'
                           CHECK (status IN ('draft','needs_review','approved','failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS media_ocr_results_owner_asset_idx
    ON public.media_ocr_results (owner_id, asset_id);

ALTER TABLE public.media_ocr_results ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.media_ocr_results;
CREATE POLICY cognix_authenticated_owner ON public.media_ocr_results
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.media_ocr_results;
CREATE POLICY cognix_deny_anonymous ON public.media_ocr_results
    FOR ALL TO anon USING (false);


-- ─── media_device_gates ───────────────────────────────────────────────────────
-- Phase 19: Records which native device capabilities are active for a user.

CREATE TABLE IF NOT EXISTS public.media_device_gates (
    id              TEXT        NOT NULL PRIMARY KEY,
    owner_id        TEXT        NOT NULL,
    capability      TEXT        NOT NULL
                                CHECK (capability IN ('camera','voice','push','biometric','offline')),
    device_verified BOOLEAN     NOT NULL DEFAULT false,
    user_enabled    BOOLEAN     NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS media_device_gates_owner_capability_idx
    ON public.media_device_gates (owner_id, capability);

ALTER TABLE public.media_device_gates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.media_device_gates;
CREATE POLICY cognix_authenticated_owner ON public.media_device_gates
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.media_device_gates;
CREATE POLICY cognix_deny_anonymous ON public.media_device_gates
    FOR ALL TO anon USING (false);
