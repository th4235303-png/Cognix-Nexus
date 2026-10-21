-- Add a covering index for the lifecycle-event foreign key.
-- This is additive and does not change row visibility or application semantics.
CREATE INDEX IF NOT EXISTS idx_agent_lifecycle_events_job_id
    ON public.agent_lifecycle_events (job_id);
