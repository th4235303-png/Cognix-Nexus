-- Search indexes for the first Brain Vault retrieval layer.
-- Uses PostgreSQL full-text search without requiring pgvector, so local and hosted
-- PostgreSQL instances remain compatible. Vector embeddings can be added later.

ALTER TABLE chunks ADD COLUMN IF NOT EXISTS search_vector tsvector
  GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;

CREATE INDEX IF NOT EXISTS idx_chunks_search_vector
  ON chunks USING GIN(search_vector);

ALTER TABLE notes ADD COLUMN IF NOT EXISTS search_vector tsvector
  GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;

CREATE INDEX IF NOT EXISTS idx_notes_search_vector
  ON notes USING GIN(search_vector);
