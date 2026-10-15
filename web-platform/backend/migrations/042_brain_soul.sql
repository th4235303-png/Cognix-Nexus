-- 042_brain_soul.sql
-- Brain Soul File: operator context store + weekly knowledge synthesis snapshots
-- Applied automatically by ensure_schema() on startup.

CREATE TABLE IF NOT EXISTS brain_soul_context (
    id           BIGSERIAL PRIMARY KEY,
    context_key  TEXT        NOT NULL,
    context_value TEXT       NOT NULL,
    description  TEXT        NOT NULL DEFAULT '',
    is_active    BOOLEAN     NOT NULL DEFAULT TRUE,
    updated_by   TEXT        NOT NULL DEFAULT 'system',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT brain_soul_context_key_uq UNIQUE (context_key)
);

CREATE TABLE IF NOT EXISTS brain_soul_syntheses (
    id               BIGSERIAL PRIMARY KEY,
    period_label     TEXT        NOT NULL,
    period_start     TIMESTAMPTZ NOT NULL,
    period_end       TIMESTAMPTZ NOT NULL,
    topic            TEXT        NOT NULL DEFAULT 'general',
    synthesis_text   TEXT        NOT NULL,
    source_item_ids  JSONB       NOT NULL DEFAULT '[]',
    item_count       INT         NOT NULL DEFAULT 0,
    provider         TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT brain_soul_syntheses_period_topic_uq UNIQUE (period_label, topic)
);

CREATE INDEX IF NOT EXISTS idx_brain_soul_syntheses_period
    ON brain_soul_syntheses (period_label);
CREATE INDEX IF NOT EXISTS idx_brain_soul_syntheses_topic
    ON brain_soul_syntheses (topic);
CREATE INDEX IF NOT EXISTS idx_brain_soul_syntheses_created
    ON brain_soul_syntheses (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_brain_soul_context_active
    ON brain_soul_context (is_active) WHERE is_active = TRUE;
