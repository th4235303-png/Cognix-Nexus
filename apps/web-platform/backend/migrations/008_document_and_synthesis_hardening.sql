-- Document assistant, richer export metadata, and reviewable contradiction state.
ALTER TABLE document_jobs
  ADD COLUMN IF NOT EXISTS content_hash TEXT,
  ADD COLUMN IF NOT EXISTS error TEXT;

ALTER TABLE synthesis_runs
  ADD COLUMN IF NOT EXISTS citations JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_document_jobs_status_updated
  ON document_jobs(status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_contradictions_status_created
  ON contradictions(status, created_at DESC);
