-- Brain Vault advanced feature schema.
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE embeddings
  ADD COLUMN IF NOT EXISTS embedding_vector vector(1536);

CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw
  ON embeddings USING hnsw (embedding_vector vector_cosine_ops)
  WHERE embedding_vector IS NOT NULL;

CREATE TABLE IF NOT EXISTS summary_sources (
  summary_id TEXT NOT NULL REFERENCES book_summaries(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(summary_id, source_type, source_id)
);

CREATE TABLE IF NOT EXISTS language_cards (
  id TEXT PRIMARY KEY,
  front TEXT NOT NULL,
  back TEXT NOT NULL,
  language TEXT NOT NULL,
  source_note TEXT,
  due_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  stability REAL NOT NULL DEFAULT 0,
  difficulty REAL NOT NULL DEFAULT 5,
  reps INTEGER NOT NULL DEFAULT 0,
  lapses INTEGER NOT NULL DEFAULT 0,
  state TEXT NOT NULL DEFAULT 'learning',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS language_reviews (
  id TEXT PRIMARY KEY,
  card_id TEXT NOT NULL REFERENCES language_cards(id) ON DELETE CASCADE,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 4),
  reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  scheduled_for TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS document_jobs (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  result JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS synthesis_runs (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  query TEXT NOT NULL,
  source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  result TEXT,
  status TEXT NOT NULL DEFAULT 'evidence_only',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS contradictions (
  id TEXT PRIMARY KEY,
  left_source_type TEXT NOT NULL,
  left_source_id TEXT NOT NULL,
  right_source_type TEXT NOT NULL,
  right_source_id TEXT NOT NULL,
  statement TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'needs_review',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vault_items (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  ciphertext TEXT NOT NULL,
  nonce TEXT NOT NULL,
  kdf_salt TEXT NOT NULL,
  kdf_params JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
