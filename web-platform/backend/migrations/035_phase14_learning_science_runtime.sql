-- Phase 14: Learning Science runtime tables.
-- learning_signals: append-only, owner-isolated, evidence-required event log.
-- learning_path_items: reviewable path records with mandatory evidence refs.
-- Both tables enforce owner isolation via RLS using the initplan-safe pattern.

-- ─── learning_signals ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.learning_signals (
    id               TEXT         PRIMARY KEY,
    owner_id         TEXT         NOT NULL,
    subject_id       TEXT         NOT NULL,
    signal_type      TEXT         NOT NULL
                     CHECK (signal_type IN ('review', 'recall', 'completion', 'difficulty', 'reflection')),
    strength         FLOAT        NOT NULL
                     CHECK (strength >= 0.0 AND strength <= 1.0),
    evidence_refs    JSONB        NOT NULL DEFAULT '[]'::jsonb,
    idempotency_key  TEXT         NOT NULL,
    occurred_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Idempotency: one signal per (key) — supports ON CONFLICT DO NOTHING.
CREATE UNIQUE INDEX IF NOT EXISTS uq_learning_signals_idempotency
    ON public.learning_signals(idempotency_key);

-- Per-owner, per-subject lookups ordered by recency (decay ranking queries).
CREATE INDEX IF NOT EXISTS idx_learning_signals_owner_subject
    ON public.learning_signals(owner_id, subject_id, occurred_at DESC);

-- Per-owner recency scan (list endpoint).
CREATE INDEX IF NOT EXISTS idx_learning_signals_owner_recent
    ON public.learning_signals(owner_id, occurred_at DESC);

-- RLS: owner isolation using initplan-safe pattern.
ALTER TABLE public.learning_signals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.learning_signals;
CREATE POLICY cognix_authenticated_owner ON public.learning_signals
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.learning_signals;
CREATE POLICY cognix_deny_anonymous ON public.learning_signals
    FOR ALL TO anon USING (false);

-- ─── learning_path_items ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.learning_path_items (
    id            TEXT         PRIMARY KEY,
    owner_id      TEXT         NOT NULL,
    subject_id    TEXT         NOT NULL,
    position      INTEGER      NOT NULL CHECK (position >= 0),
    reason        TEXT         NOT NULL CHECK (char_length(reason) > 0),
    evidence_refs JSONB        NOT NULL DEFAULT '[]'::jsonb,
    review_state  TEXT         NOT NULL DEFAULT 'draft'
                  CHECK (review_state IN ('draft', 'active', 'completed', 'skipped')),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Lookups by owner and review state.
CREATE INDEX IF NOT EXISTS idx_learning_path_items_owner
    ON public.learning_path_items(owner_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_learning_path_items_active
    ON public.learning_path_items(owner_id, position)
    WHERE review_state = 'active';

-- RLS: owner isolation.
ALTER TABLE public.learning_path_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.learning_path_items;
CREATE POLICY cognix_authenticated_owner ON public.learning_path_items
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.learning_path_items;
CREATE POLICY cognix_deny_anonymous ON public.learning_path_items
    FOR ALL TO anon USING (false);
