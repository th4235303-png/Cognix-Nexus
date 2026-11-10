-- Prevent duplicate owner-bound flashcards generated repeatedly from the same source.
-- Legacy records without source/question metadata are intentionally excluded.
CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_reviews_owner_source_question
  ON public.learning_reviews(owner_id, (metadata->>'source_id'), (metadata->>'question'))
  WHERE (metadata->>'source_id') IS NOT NULL AND (metadata->>'question') IS NOT NULL;
