-- Durable production schema baseline. Applied automatically when DATABASE_URL is configured.
CREATE TABLE sources (
  id TEXT PRIMARY KEY, url TEXT NOT NULL UNIQUE, title TEXT, status TEXT NOT NULL,
  processing_stage TEXT NOT NULL, source_trust TEXT, original_text TEXT,
  ai_summary TEXT, myanmar_translation TEXT, human_edited_myanmar TEXT,
  approved_myanmar TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE processing_tasks (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
  stage TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL,
  retry_count INTEGER NOT NULL DEFAULT 0, error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE claims (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
  claim_text TEXT NOT NULL, excerpt TEXT, location TEXT, confidence NUMERIC,
  verification_state TEXT NOT NULL
);
CREATE TABLE reviews (
  source_id TEXT PRIMARY KEY REFERENCES sources(id), status TEXT NOT NULL,
  reviewer_id TEXT, note TEXT, reviewed_at TIMESTAMPTZ
);
CREATE TABLE export_jobs (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
  destination TEXT NOT NULL, status TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE,
  safe_reference TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE activity_events (
  id TEXT PRIMARY KEY, action TEXT NOT NULL, target TEXT NOT NULL,
  previous_state TEXT, new_state TEXT, actor_id TEXT, request_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
