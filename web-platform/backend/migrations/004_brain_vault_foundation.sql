-- Brain Vault foundation schema.
-- This migration is intentionally storage-neutral: book content is durable in PostgreSQL,
-- while original binary storage can be added behind a storage adapter later.

CREATE TABLE IF NOT EXISTS books (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  language TEXT NOT NULL DEFAULT 'en',
  file_type TEXT NOT NULL,
  source_kind TEXT NOT NULL DEFAULT 'upload',
  source_url TEXT,
  status TEXT NOT NULL DEFAULT 'ready',
  description TEXT,
  content_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chapters (
  id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  chapter_number INTEGER NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(book_id, chapter_number)
);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  sequence INTEGER NOT NULL,
  content TEXT NOT NULL,
  page_number INTEGER,
  start_offset INTEGER,
  end_offset INTEGER,
  token_count INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(chapter_id, sequence)
);

CREATE TABLE IF NOT EXISTS book_summaries (
  id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  level TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  model TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(book_id, level, version)
);

CREATE TABLE IF NOT EXISTS notes (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  note_type TEXT NOT NULL DEFAULT 'note',
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS note_sources (
  note_id TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(note_id, source_type, source_id)
);

CREATE TABLE IF NOT EXISTS concepts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS concept_links (
  id TEXT PRIMARY KEY,
  from_concept_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  to_concept_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  relation TEXT NOT NULL DEFAULT 'related',
  weight NUMERIC NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(from_concept_id, to_concept_id, relation)
);

CREATE TABLE IF NOT EXISTS embeddings (
  id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding JSONB,
  model TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(owner_type, owner_id)
);

CREATE INDEX IF NOT EXISTS idx_books_updated_at ON books(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chapters_book_number ON chapters(book_id, chapter_number);
CREATE INDEX IF NOT EXISTS idx_chunks_chapter_sequence ON chunks(chapter_id, sequence);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_note_sources_lookup ON note_sources(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_concept_links_from ON concept_links(from_concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_links_to ON concept_links(to_concept_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_owner ON embeddings(owner_type, owner_id);
