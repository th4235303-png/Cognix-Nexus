-- Phase 22: complete the Book Intelligence acceptance schema.
-- Additive only: existing summary/lesson rows remain valid and receive empty
-- lineage/item arrays until new writes populate them.
ALTER TABLE public.book_summaries
    ADD COLUMN IF NOT EXISTS source_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE public.lesson_packs
    ADD COLUMN IF NOT EXISTS items JSONB NOT NULL DEFAULT '[]'::jsonb;
