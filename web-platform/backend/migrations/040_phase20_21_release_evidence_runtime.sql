-- Phase 20/21: Release Evidence and Operational Readiness runtime
-- Migration 040
-- Tables: release_gate_evidence, release_recovery_drills, release_decisions
-- RLS: initplan-safe pattern (SELECT current_setting(...)) — never session-level

-- ─── release_gate_evidence ────────────────────────────────────────────────────
-- Stores gate evidence records for release readiness evaluation.
-- Idempotency key prevents duplicate gate/status combinations per owner.

CREATE TABLE IF NOT EXISTS public.release_gate_evidence (
    id               TEXT        NOT NULL PRIMARY KEY,
    owner_id         TEXT        NOT NULL,
    gate_id          TEXT        NOT NULL,
    status           TEXT        NOT NULL
                                 CHECK (status IN ('pending','pass','fail','blocked')),
    evidence_ref     TEXT,
    observed_at      TEXT,
    idempotency_key  TEXT        NOT NULL UNIQUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS release_gate_evidence_owner_idx
    ON public.release_gate_evidence (owner_id);

CREATE INDEX IF NOT EXISTS release_gate_evidence_gate_id_idx
    ON public.release_gate_evidence (owner_id, gate_id);

ALTER TABLE public.release_gate_evidence ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.release_gate_evidence;
CREATE POLICY cognix_authenticated_owner ON public.release_gate_evidence
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.release_gate_evidence;
CREATE POLICY cognix_deny_anonymous ON public.release_gate_evidence
    FOR ALL TO anon USING (false);


-- ─── release_recovery_drills ──────────────────────────────────────────────────
-- Stores completed recovery drill results (observed + recovered + evidenced only).

CREATE TABLE IF NOT EXISTS public.release_recovery_drills (
    id           TEXT        NOT NULL PRIMARY KEY,
    owner_id     TEXT        NOT NULL,
    drill_id     TEXT        NOT NULL,
    kind         TEXT        NOT NULL
                             CHECK (kind IN ('backup_restore','rollback','failover')),
    observed     BOOLEAN     NOT NULL DEFAULT false,
    recovered    BOOLEAN     NOT NULL DEFAULT false,
    evidence_ref TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS release_recovery_drills_owner_idx
    ON public.release_recovery_drills (owner_id);

CREATE INDEX IF NOT EXISTS release_recovery_drills_drill_id_idx
    ON public.release_recovery_drills (owner_id, drill_id);

ALTER TABLE public.release_recovery_drills ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.release_recovery_drills;
CREATE POLICY cognix_authenticated_owner ON public.release_recovery_drills
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.release_recovery_drills;
CREATE POLICY cognix_deny_anonymous ON public.release_recovery_drills
    FOR ALL TO anon USING (false);


-- ─── release_decisions ────────────────────────────────────────────────────────
-- Stores phase 21 release decisions with JSONB evidence snapshot.

CREATE TABLE IF NOT EXISTS public.release_decisions (
    id         TEXT        NOT NULL PRIMARY KEY,
    owner_id   TEXT        NOT NULL,
    revision   TEXT        NOT NULL,
    approved   BOOLEAN     NOT NULL DEFAULT false,
    evidence   JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS release_decisions_owner_revision_idx
    ON public.release_decisions (owner_id, revision);

ALTER TABLE public.release_decisions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cognix_authenticated_owner ON public.release_decisions;
CREATE POLICY cognix_authenticated_owner ON public.release_decisions
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));

DROP POLICY IF EXISTS cognix_deny_anonymous ON public.release_decisions;
CREATE POLICY cognix_deny_anonymous ON public.release_decisions
    FOR ALL TO anon USING (false);
