-- Cognix Core schema alignment for the current API contract.
-- Apply after 001_initial.sql.

ALTER TABLE sources
  ADD COLUMN IF NOT EXISTS note TEXT,
  ADD COLUMN IF NOT EXISTS critical_warnings JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE processing_tasks
  ADD COLUMN IF NOT EXISTS error TEXT;

ALTER TABLE claims
  ALTER COLUMN confidence TYPE TEXT USING confidence::text,
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE reviews
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE export_jobs
  ADD COLUMN IF NOT EXISTS files JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS drive_reference TEXT;

CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_updated_at ON sources(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_source_id ON processing_tasks(source_id);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_status ON processing_tasks(status);
CREATE INDEX IF NOT EXISTS idx_claims_source_id ON claims(source_id);
CREATE INDEX IF NOT EXISTS idx_export_jobs_source_id ON export_jobs(source_id);
CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status);
CREATE INDEX IF NOT EXISTS idx_activity_events_target_created_at ON activity_events(target, created_at DESC);
