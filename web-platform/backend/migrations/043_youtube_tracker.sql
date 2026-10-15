-- Migration 043: YouTube Channel Auto-Tracker
-- Creates tables for tracking YouTube channels and their videos

CREATE TABLE IF NOT EXISTS youtube_channels (
    id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL UNIQUE,        -- YouTube channel ID (UCxxx)
    channel_url TEXT NOT NULL,
    channel_name TEXT,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    poll_interval_hours INTEGER NOT NULL DEFAULT 6,
    last_polled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS brain_youtube_videos (
    id BIGSERIAL PRIMARY KEY,
    channel_id TEXT NOT NULL REFERENCES youtube_channels(channel_id) ON DELETE CASCADE,
    video_id TEXT NOT NULL UNIQUE,
    title TEXT,
    published_at TIMESTAMPTZ,
    transcript_fetched BOOLEAN NOT NULL DEFAULT FALSE,
    transcript_text TEXT,
    summary TEXT,
    key_points JSONB,
    llm_processed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_byt_channel ON brain_youtube_videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_byt_published ON brain_youtube_videos(published_at DESC);
