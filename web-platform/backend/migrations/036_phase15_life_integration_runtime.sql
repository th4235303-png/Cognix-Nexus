-- Phase 15: Life Integration runtime tables.
-- life_restore_requests: explicit user-triggered context restores (never implicit).
-- life_consent_events:  append-only consent grant/revocation audit log.
-- life_capsule_refs:    encrypted capsule metadata (ciphertext reference only — never ciphertext).
-- All tables enforce owner isolation via RLS using the initplan-safe pattern.

-- ─── life_restore_requests ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.life_restore_requests (
    id                TEXT        PRIMARY KEY,
    owner_id          TEXT        NOT NULL,
    scope             JSONB       NOT NULL DEFAULT '[]'::jsonb,
    reason            TEXT        NOT NULL CHECK (char_length(reason) > 0),
    requested_by_user BOOLEAN     NOT NULL DEFAULT TRUE,
    idempotency_key   TEXT        NOT NULL,
    status            TEXT        NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'applied', 'denied', 'expired')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One restore per idempotency_key.
CREATE UNIQUE INDEX IF NOT EXISTS uq_life_restore_requests_idempotency
    ON public.life_restore_requests(idempotency_key);

-- Owner recency lookup.
CREATE INDEX IF NOT EXISTS idx_life_restore_requests_owner
    ON public.life_restore_requests(owner_id, created_at DESC);

-- Only explicit user-triggered restores are stored (invariant guard at DB level).
CREATE INDEX IF NOT EXISTS idx_life_restore_user_triggered
    ON public.life_restore_requests(owner_id)
    WHERE requested_by_user = TRUE;

-- RLS: owner isolation using initplan-safe pattern.
ALTER TABLE public.life_restore_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.life_restore_requests;
CREATE POLICY cognix_authenticated_owner ON public.life_restore_requests
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.life_restore_requests;
CREATE POLICY cognix_deny_anonymous ON public.life_restore_requests
    FOR ALL TO anon USING (false);

-- ─── life_consent_events ─────────────────────────────────────────────────────
-- Append-only audit log.  Revocation adds a new row — no UPDATE, no DELETE.
CREATE TABLE IF NOT EXISTS public.life_consent_events (
    id              TEXT        PRIMARY KEY,
    owner_id        TEXT        NOT NULL,
    feature_scope   TEXT        NOT NULL CHECK (char_length(feature_scope) > 0),
    action          TEXT        NOT NULL CHECK (action IN ('granted', 'revoked')),
    idempotency_key TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Idempotency: one event per key.
CREATE UNIQUE INDEX IF NOT EXISTS uq_life_consent_events_idempotency
    ON public.life_consent_events(idempotency_key);

-- Per-owner, per-scope lookup (most recent action wins).
CREATE INDEX IF NOT EXISTS idx_life_consent_events_owner_scope
    ON public.life_consent_events(owner_id, feature_scope, created_at DESC);

-- RLS: owner isolation.
ALTER TABLE public.life_consent_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.life_consent_events;
CREATE POLICY cognix_authenticated_owner ON public.life_consent_events
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.life_consent_events;
CREATE POLICY cognix_deny_anonymous ON public.life_consent_events
    FOR ALL TO anon USING (false);

-- ─── life_capsule_refs ────────────────────────────────────────────────────────
-- Metadata only — ciphertext_ref is a URI/key reference; actual ciphertext is NEVER stored here.
CREATE TABLE IF NOT EXISTS public.life_capsule_refs (
    id              TEXT        PRIMARY KEY,
    owner_id        TEXT        NOT NULL,
    ciphertext_ref  TEXT        NOT NULL CHECK (char_length(ciphertext_ref) > 0),
    algorithm       TEXT        NOT NULL CHECK (algorithm IN ('AES-256-GCM', 'ChaCha20-Poly1305')),
    exportable      BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-owner capsule lookup.
CREATE INDEX IF NOT EXISTS idx_life_capsule_refs_owner
    ON public.life_capsule_refs(owner_id, created_at DESC);

-- RLS: owner isolation.
ALTER TABLE public.life_capsule_refs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.life_capsule_refs;
CREATE POLICY cognix_authenticated_owner ON public.life_capsule_refs
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.life_capsule_refs;
CREATE POLICY cognix_deny_anonymous ON public.life_capsule_refs
    FOR ALL TO anon USING (false);
