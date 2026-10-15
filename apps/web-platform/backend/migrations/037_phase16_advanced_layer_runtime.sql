-- Phase 16: Advanced Layer runtime tables.
-- advanced_wiki_entities:     private wiki with mandatory source lineage.
-- advanced_growth_metrics:    explainable, evidence-bound growth tracking.
-- advanced_offline_handoffs:  export/recovery artifact refs (no payload stored).
-- advanced_secret_refs:       encrypted secret metadata (ciphertext ref only).
-- All tables use RLS with the initplan-safe pattern.

-- ─── advanced_wiki_entities ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.advanced_wiki_entities (
    id           TEXT        PRIMARY KEY,
    owner_id     TEXT        NOT NULL,
    name         TEXT        NOT NULL CHECK (char_length(name) > 0),
    entity_type  TEXT        NOT NULL,
    source_refs  JSONB       NOT NULL DEFAULT '[]'::jsonb,
    review_state TEXT        NOT NULL DEFAULT 'draft'
                 CHECK (review_state IN ('draft', 'needs_review', 'approved', 'rejected')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_advanced_wiki_entities_owner
    ON public.advanced_wiki_entities(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_advanced_wiki_entities_type
    ON public.advanced_wiki_entities(owner_id, entity_type);

ALTER TABLE public.advanced_wiki_entities ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.advanced_wiki_entities;
CREATE POLICY cognix_authenticated_owner ON public.advanced_wiki_entities
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.advanced_wiki_entities;
CREATE POLICY cognix_deny_anonymous ON public.advanced_wiki_entities
    FOR ALL TO anon USING (false);

-- ─── advanced_growth_metrics ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.advanced_growth_metrics (
    id            TEXT        PRIMARY KEY,
    owner_id      TEXT        NOT NULL,
    metric        TEXT        NOT NULL CHECK (char_length(metric) > 0),
    value         FLOAT       NOT NULL,
    unit          TEXT        NOT NULL CHECK (char_length(unit) > 0),
    evidence_refs JSONB       NOT NULL DEFAULT '[]'::jsonb,
    derivation    TEXT        NOT NULL CHECK (char_length(derivation) > 0),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_advanced_growth_metrics_owner
    ON public.advanced_growth_metrics(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_advanced_growth_metrics_metric
    ON public.advanced_growth_metrics(owner_id, metric, created_at DESC);

ALTER TABLE public.advanced_growth_metrics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.advanced_growth_metrics;
CREATE POLICY cognix_authenticated_owner ON public.advanced_growth_metrics
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.advanced_growth_metrics;
CREATE POLICY cognix_deny_anonymous ON public.advanced_growth_metrics
    FOR ALL TO anon USING (false);

-- ─── advanced_offline_handoffs ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.advanced_offline_handoffs (
    id           TEXT        PRIMARY KEY,
    owner_id     TEXT        NOT NULL,
    format       TEXT        NOT NULL
                 CHECK (format IN ('encrypted_archive', 'signed_manifest')),
    artifact_ref TEXT        NOT NULL CHECK (char_length(artifact_ref) > 0),
    recoverable  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_advanced_offline_handoffs_owner
    ON public.advanced_offline_handoffs(owner_id, created_at DESC);

ALTER TABLE public.advanced_offline_handoffs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.advanced_offline_handoffs;
CREATE POLICY cognix_authenticated_owner ON public.advanced_offline_handoffs
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.advanced_offline_handoffs;
CREATE POLICY cognix_deny_anonymous ON public.advanced_offline_handoffs
    FOR ALL TO anon USING (false);

-- ─── advanced_secret_refs ─────────────────────────────────────────────────────
-- Stores ciphertext_ref (URI) only — raw secrets are NEVER stored here.
CREATE TABLE IF NOT EXISTS public.advanced_secret_refs (
    id              TEXT        PRIMARY KEY,
    owner_id        TEXT        NOT NULL,
    kind            TEXT        NOT NULL
                    CHECK (kind IN ('totp', 'ssh_key', 'credential')),
    ciphertext_ref  TEXT        NOT NULL CHECK (char_length(ciphertext_ref) > 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_advanced_secret_refs_owner
    ON public.advanced_secret_refs(owner_id, created_at DESC);

ALTER TABLE public.advanced_secret_refs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.advanced_secret_refs;
CREATE POLICY cognix_authenticated_owner ON public.advanced_secret_refs
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.advanced_secret_refs;
CREATE POLICY cognix_deny_anonymous ON public.advanced_secret_refs
    FOR ALL TO anon USING (false);
