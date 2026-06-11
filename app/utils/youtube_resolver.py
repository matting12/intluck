"""
Resolve YouTube channel URLs to actual video URLs via the YouTube Data API.

This is a fallback for when Brave Search returns a channel page instead of
a specific video. YouTube's RSS feed is no longer reliable (returns 404),
so resolution requires YOUTUBE_API_KEY to be set.

If no API key is configured, channel URLs are returned unchanged (the frontend
renders them as a plain link rather than an embed).

To enable: add YOUTUBE_API_KEY=... to your .env
Get a free key at console.cloud.google.com (10,000 quota units/day; this
function uses only 2 units per call — channels.list + playlistItems.list).
"""

import re
import os
import logging

import httpx
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


_CHANNEL_SUFFIX = r"(?:/(?:videos|about|featured|shorts|playlists|community|channels|streams))?"

def _parse_channel_url(url: str):
    """
    Return (identifier, id_type) when the URL is a YouTube channel/user page,
    or None if it's already a video watch URL (or unrecognised format).

    Handles common channel page suffixes (/videos, /about, /featured, etc.)
    and mobile URLs (m.youtube.com).

    id_type: 'channel_id' | 'handle' | 'username' | 'custom'
    """
    try:
        path = urlparse(url).path.rstrip("/")

        m = re.match(r"^/channel/([A-Za-z0-9_-]+)" + _CHANNEL_SUFFIX + r"$", path)
        if m:
            return (m.group(1), "channel_id")

        m = re.match(r"^/@([A-Za-z0-9_.\-]+)" + _CHANNEL_SUFFIX + r"$", path)
        if m:
            return (m.group(1), "handle")

        m = re.match(r"^/user/([A-Za-z0-9_.\-]+)" + _CHANNEL_SUFFIX + r"$", path)
        if m:
            return (m.group(1), "username")

        m = re.match(r"^/c/([A-Za-z0-9_.\-]+)" + _CHANNEL_SUFFIX + r"$", path)
        if m:
            return (m.group(1), "custom")

        return None
    except Exception:
        return None


def _uploads_playlist_id(channel_id: str) -> str:
    """Convert a UC... channel_id to its UU... uploads playlist id."""
    if channel_id.startswith("UC"):
        return "UU" + channel_id[2:]
    return channel_id


async def _resolve_via_api(identifier: str, id_type: str, api_key: str):
    """
    Use the YouTube Data API to get the most recent video from a channel.
    Returns a dict with url/title/description, or None on any failure.
    Uses 2 quota units: channels.list (1) + playlistItems.list (1).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: resolve identifier → channel_id
            if id_type == "channel_id":
                channel_id = identifier
            elif id_type == "handle":
                resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id", "forHandle": identifier, "key": api_key},
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if not items:
                    logger.warning("YouTube API: no channel for handle=%s", identifier)
                    return None
                channel_id = items[0]["id"]
            elif id_type in ("username", "custom"):
                param_key = "forUsername" if id_type == "username" else "forHandle"
                resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id", param_key: identifier, "key": api_key},
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if not items:
                    return None
                channel_id = items[0]["id"]
            else:
                return None

            # Step 2: fetch first item from uploads playlist (1 quota unit)
            uploads_id = _uploads_playlist_id(channel_id)
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={
                    "part": "snippet",
                    "playlistId": uploads_id,
                    "maxResults": 1,
                    "key": api_key,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                logger.warning("YouTube API: uploads playlist empty for channel_id=%s", channel_id)
                return None

            snippet = items[0]["snippet"]
            vid = snippet["resourceId"]["videoId"]
            title = snippet.get("title", "")
            description = (snippet.get("description") or "")[:300]

            return {
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": title,
                "description": description,
            }

    except Exception as e:
        logger.warning("YouTube API resolution failed (id=%s type=%s): %s", identifier, id_type, e)
        return None


async def resolve_youtube_channel_to_video(link: dict) -> dict:
    """
    If `link` is a YouTube channel URL, attempt to resolve it to the most
    recent video using the YouTube Data API.

    Returns the original link unchanged if:
    - it's already a video URL (/watch?v=...)
    - no YOUTUBE_API_KEY is configured
    - the API call fails for any reason
    """
    url = link.get("url", "")
    if "youtube.com" not in url and "youtu.be" not in url:
        return link

    parsed = _parse_channel_url(url)
    if parsed is None:
        # Already a video/watch URL — nothing to do
        return link

    if not YOUTUBE_API_KEY:
        logger.debug(
            "Channel URL %s found but YOUTUBE_API_KEY not set; keeping channel link", url
        )
        return link

    identifier, id_type = parsed
    resolved = await _resolve_via_api(identifier, id_type, YOUTUBE_API_KEY)

    if resolved is None:
        logger.info("Could not resolve channel URL to video, keeping channel link: %s", url)
        return link

    updated = link.copy()
    updated["url"] = resolved["url"]
    if resolved.get("title"):
        updated["title"] = resolved["title"]
    if resolved.get("description") is not None:
        updated["description"] = resolved["description"]

    logger.info(
        "Resolved channel %s → %s (%s)",
        url,
        resolved["url"],
        updated.get("title", "")[:60],
    )
    return updated
