-- Phase 17: Cognix Core Integration runtime tables.
-- core_artifacts:                    EvidenceBoundArtifact — evidence-gated, needs human review.
-- core_document_classifications:     DocumentClassification — confidence-validated.
-- core_documents:                    Document lifecycle state machine.
-- core_parallel_texts:               ParallelText — language pair validated.
-- All tables use RLS with the initplan-safe pattern.

-- ─── core_artifacts ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.core_artifacts (
    id            TEXT        PRIMARY KEY,
    owner_id      TEXT        NOT NULL,
    artifact_type TEXT        NOT NULL
                  CHECK (artifact_type IN (
                      'claim','translation','fact_check','research_report',
                      'document','ocr_review','parallel_text','tutor_correction'
                  )),
    evidence_refs JSONB       NOT NULL DEFAULT '[]'::jsonb,
    payload       JSONB       NOT NULL DEFAULT '{}'::jsonb,
    review_state  TEXT        NOT NULL DEFAULT 'needs_review'
                  CHECK (review_state IN ('draft','needs_review','approved','rejected')),
    reviewed_at   TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_core_artifacts_owner
    ON public.core_artifacts(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_core_artifacts_review_pending
    ON public.core_artifacts(owner_id)
    WHERE review_state = 'needs_review';

ALTER TABLE public.core_artifacts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cognix_authenticated_owner ON public.core_artifacts;
CREATE POLICY cognix_authenticated_owner ON public.core_artifacts
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));
DROP POLICY IF EXISTS cognix_deny_anonymous ON public.core_artifacts;
CREATE POLICY cognix_deny_anonymous ON public.core_artifacts
    FOR ALL TO anon USING (false);

-- ─── core_document_classifications ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.core_document_classifications (
    id            TEXT        PRIMARY KEY,
    owner_id      TEXT        NOT NULL,
    document_id   TEXT        NOT NULL,
    document_type TEXT        NOT NULL
                  CHECK (document_type IN (
                      'contract','letter','form','invoice','receipt',
                      'meeting_note','study_material','medical_report',
                      'legal_notice','business_card'
                  )),
    confidence    FLOAT       NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_core_doc_classifications_owner
    ON public.core_document_classifications(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_core_doc_classifications_doc
    ON public.core_document_classifications(document_id);

ALTER TABLE public.core_document_classifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cognix_authenticated_owner ON public.core_document_classifications;
CREATE POLICY cognix_authenticated_owner ON public.core_document_classifications
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));
DROP POLICY IF EXISTS cognix_deny_anonymous ON public.core_document_classifications;
CREATE POLICY cognix_deny_anonymous ON public.core_document_classifications
    FOR ALL TO anon USING (false);

-- ─── core_documents ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.core_documents (
    id               TEXT        PRIMARY KEY,
    owner_id         TEXT        NOT NULL,
    title            TEXT        NOT NULL CHECK (char_length(title) > 0),
    lifecycle_state  TEXT        NOT NULL DEFAULT 'inbox'
                     CHECK (lifecycle_state IN (
                         'inbox','processing','review','approved','indexed','archived','deleted'
                     )),
    source_ref       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_core_documents_owner
    ON public.core_documents(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_core_documents_state
    ON public.core_documents(owner_id, lifecycle_state);

ALTER TABLE public.core_documents ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cognix_authenticated_owner ON public.core_documents;
CREATE POLICY cognix_authenticated_owner ON public.core_documents
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));
DROP POLICY IF EXISTS cognix_deny_anonymous ON public.core_documents;
CREATE POLICY cognix_deny_anonymous ON public.core_documents
    FOR ALL TO anon USING (false);

-- ─── core_parallel_texts ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.core_parallel_texts (
    id               TEXT        PRIMARY KEY,
    owner_id         TEXT        NOT NULL,
    source_language  TEXT        NOT NULL CHECK (source_language IN ('my','ja','ko')),
    target_language  TEXT        NOT NULL CHECK (target_language IN ('my','ja','ko')),
    source           TEXT        NOT NULL CHECK (char_length(source) > 0),
    translation      TEXT        NOT NULL CHECK (char_length(translation) > 0),
    reading          TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_core_parallel_texts_owner
    ON public.core_parallel_texts(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_core_parallel_texts_lang_pair
    ON public.core_parallel_texts(owner_id, source_language, target_language);

ALTER TABLE public.core_parallel_texts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cognix_authenticated_owner ON public.core_parallel_texts;
CREATE POLICY cognix_authenticated_owner ON public.core_parallel_texts
    FOR ALL TO authenticated
    USING  (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)))
    WITH CHECK (owner_id IS NOT NULL AND owner_id = (SELECT current_setting('request.jwt.claim.sub', true)));
DROP POLICY IF EXISTS cognix_deny_anonymous ON public.core_parallel_texts;
CREATE POLICY cognix_deny_anonymous ON public.core_parallel_texts
    FOR ALL TO anon USING (false);
