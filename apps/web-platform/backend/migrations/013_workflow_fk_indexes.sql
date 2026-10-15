CREATE INDEX IF NOT EXISTS idx_agent_findings_job_id ON public.agent_findings(job_id);
CREATE INDEX IF NOT EXISTS idx_language_reviews_card_id ON public.language_reviews(card_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_source_job_id ON public.media_assets(source_job_id);
CREATE INDEX IF NOT EXISTS idx_media_reviews_media_id ON public.media_reviews(media_id);
CREATE INDEX IF NOT EXISTS idx_research_reviews_report_id ON public.research_reviews(report_id);
