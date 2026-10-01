-- Vizora Lens media input boundary.
CREATE TABLE IF NOT EXISTS media_assets (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  media_type TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  source_job_id TEXT REFERENCES document_jobs(id) ON DELETE SET NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_media_assets_created_at
  ON media_assets(created_at DESC);
