-- Phase 13: AI Active Layer runtime tables.
-- agent_lifecycle_events: durable append-only event log for every agent run transition.
-- agent_decisions: persisted DecisionRecord contracts with evidence references.
-- Both tables enforce owner isolation via RLS and use idempotency keys.

-- ─── agent_lifecycle_events ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_lifecycle_events (
    id              TEXT        PRIMARY KEY,
    run_id          TEXT        NOT NULL,
    job_id          TEXT        REFERENCES public.agent_jobs(id) ON DELETE CASCADE,
    owner_id        TEXT        NOT NULL,
    event_type      TEXT        NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    idempotency_key TEXT        NOT NULL,
    metadata        JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Prevent duplicate lifecycle events for the same run transition.
CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_lifecycle_events_idempotency
    ON public.agent_lifecycle_events(idempotency_key);

-- Efficient per-run event lookup (ordered by time for lifecycle reconstruction).
CREATE INDEX IF NOT EXISTS idx_agent_lifecycle_events_run_id
    ON public.agent_lifecycle_events(run_id, occurred_at);

-- Owner-scoped event lookup.
CREATE INDEX IF NOT EXISTS idx_agent_lifecycle_events_owner
    ON public.agent_lifecycle_events(owner_id, occurred_at DESC);

-- RLS: owner isolation using initplan-safe pattern.
ALTER TABLE public.agent_lifecycle_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cognix_authenticated_owner ON public.agent_lifecycle_events;
CREATE POLICY cognix_authenticated_owner ON public.agent_lifecycle_events
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

-- Deny unauthenticated access.
DROP POLICY IF EXISTS cognix_deny_anonymous ON public.agent_lifecycle_events;
CREATE POLICY cognix_deny_anonymous ON public.agent_lifecycle_events
    FOR ALL TO anon USING (false);

-- ─── agent_decisions ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_decisions (
    id            TEXT        PRIMARY KEY,
    job_id        TEXT        REFERENCES public.agent_jobs(id) ON DELETE CASCADE,
    owner_id      TEXT        NOT NULL,
    decision      TEXT        NOT NULL,
    rationale     TEXT        NOT NULL,
    evidence      JSONB       NOT NULL DEFAULT '[]'::jsonb,
    approved_by   TEXT,
    review_state  TEXT        NOT NULL DEFAULT 'draft'
                  CHECK (review_state IN ('draft', 'needs_review', 'approved', 'rejected')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Evidence must always be attached before approval.
CREATE INDEX IF NOT EXISTS idx_agent_decisions_job
    ON public.agent_decisions(job_id);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_owner
    ON public.agent_decisions(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_review_state
    ON public.agent_decisions(review_state)
    WHERE review_state = 'needs_review';

-- RLS: owner isolation.
ALTER TABLE public.agent_decisions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cognix_authenticated_owner ON public.agent_decisions;
CREATE POLICY cognix_authenticated_owner ON public.agent_decisions
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.agent_decisions;
CREATE POLICY cognix_deny_anonymous ON public.agent_decisions
    FOR ALL TO anon USING (false);

-- ─── agent_runs: add evidence_refs column if not present ────────────────────
-- Evidence references are stored as JSONB array of EvidenceRef contracts.
ALTER TABLE public.agent_runs
    ADD COLUMN IF NOT EXISTS evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS decision_ids  JSONB NOT NULL DEFAULT '[]'::jsonb;

-- ─── observability_events: ensure event_type index exists ───────────────────
CREATE INDEX IF NOT EXISTS idx_observability_events_type
    ON public.observability_events(event_type, created_at DESC);
