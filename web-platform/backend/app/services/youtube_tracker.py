"""
YouTube Channel RSS tracker — no API key needed.
Uses YouTube's public RSS feed: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
Transcript fetch via youtube-transcript-api.
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import feedparser  # pip install feedparser

log = logging.getLogger("cognix.youtube_tracker")


def extract_channel_id(url: str) -> Optional[str]:
    """Extract YouTube channel ID from various URL formats."""
    # Handle direct channel ID input
    if re.match(r'^UC[\w-]{22}$', url.strip()):
        return url.strip()
    # Handle https://www.youtube.com/channel/UCxxx
    m = re.search(r'youtube\.com/channel/(UC[\w-]{22})', url)
    if m:
        return m.group(1)
    # Handle https://www.youtube.com/@handle — needs RSS fallback
    # For handle URLs, try to find channel ID via RSS
    return None


def fetch_channel_feed(channel_id: str) -> list[dict]:
    """Fetch latest videos from YouTube RSS feed. Returns list of video dicts."""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        feed = feedparser.parse(rss_url)
        videos = []
        for entry in feed.entries:
            video_id = entry.get('yt_videoid') or entry.get('id', '').split(':')[-1]
            videos.append({
                'video_id': video_id,
                'title': entry.get('title', ''),
                'published_at': entry.get('published', None),
            })
        return videos
    except Exception as e:
        log.error(f"RSS fetch failed for channel {channel_id}: {e}")
        return []


def fetch_transcript(video_id: str, max_chars: int = 8000) -> Optional[str]:
    """Fetch transcript for a YouTube video. Returns text or None."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'my', 'zh', 'ja', 'ko'])
        text = ' '.join([t['text'] for t in transcript_list])
        return text[:max_chars]  # Limit to avoid token overflow
    except Exception as e:
        log.warning(f"Transcript unavailable for video {video_id}: {e}")
        return None


async def summarize_video(title: str, transcript: str, llm_provider) -> dict:
    """Use LLM to summarize video transcript. Returns {summary, key_points}."""
    system_prompt = (
        "You are a knowledge assistant. Summarize the YouTube video transcript into "
        "a concise paragraph and extract 3-5 key points as a JSON list. "
        "Respond in JSON format: {\"summary\": \"...\", \"key_points\": [\"...\", \"...\"]}"
    )
    user_prompt = f"Video Title: {title}\n\nTranscript:\n{transcript}"
    try:
        response = await llm_provider.complete(system_prompt, user_prompt)
        data = json.loads(response)
        return {
            'summary': data.get('summary', response[:500]),
            'key_points': data.get('key_points', [])
        }
    except Exception as e:
        log.warning(f"LLM summarize failed: {e}")
        # Extractive fallback
        snippet = transcript[:500] if transcript else ""
        return {'summary': snippet, 'key_points': []}
