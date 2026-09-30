-- Production persistence hardening.

CREATE INDEX IF NOT EXISTS idx_sources_normalized_url
  ON sources (rtrim(url, '/'));

CREATE INDEX IF NOT EXISTS idx_sources_processing_stage
  ON sources(processing_stage);

CREATE INDEX IF NOT EXISTS idx_reviews_status
  ON reviews(status);

CREATE INDEX IF NOT EXISTS idx_export_jobs_idempotency_key
  ON export_jobs(idempotency_key);

CREATE INDEX IF NOT EXISTS idx_activity_events_created_at
  ON activity_events(created_at DESC);
