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
    Use the YouTube Data API to get the best video from a channel.
    Prefers the channel's featured/unsubscribed trailer; falls back to the
    most recent upload if no trailer is set.

    Quota cost: 2 units (channels.list + videos.list or playlistItems.list).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: resolve identifier → channel_id + fetch brandingSettings
            # (combined into one call for handle/username/custom; separate for channel_id)
            if id_type == "channel_id":
                channel_id = identifier
                resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "brandingSettings", "id": channel_id, "key": api_key},
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                branding = items[0].get("brandingSettings", {}).get("channel", {}) if items else {}
            elif id_type == "handle":
                resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id,brandingSettings", "forHandle": identifier, "key": api_key},
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if not items:
                    logger.warning("YouTube API: no channel for handle=%s", identifier)
                    return None
                channel_id = items[0]["id"]
                branding = items[0].get("brandingSettings", {}).get("channel", {})
            elif id_type in ("username", "custom"):
                param_key = "forUsername" if id_type == "username" else "forHandle"
                resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id,brandingSettings", param_key: identifier, "key": api_key},
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if not items:
                    return None
                channel_id = items[0]["id"]
                branding = items[0].get("brandingSettings", {}).get("channel", {})
            else:
                return None

            # Step 2a: try the channel's featured/unsubscribed trailer first
            trailer_id = branding.get("unsubscribedTrailer")
            if trailer_id:
                resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={"part": "snippet", "id": trailer_id, "key": api_key},
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if items:
                    snippet = items[0]["snippet"]
                    logger.info("YouTube: using featured trailer %s for channel %s", trailer_id, channel_id)
                    return {
                        "url": f"https://www.youtube.com/watch?v={trailer_id}",
                        "title": snippet.get("title", ""),
                        "description": (snippet.get("description") or "")[:300],
                    }

            # Step 2b: fall back to most recent upload from uploads playlist
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
            return {
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": snippet.get("title", ""),
                "description": (snippet.get("description") or "")[:300],
            }

    except Exception as e:
        logger.warning("YouTube API resolution failed (id=%s type=%s): %s", identifier, id_type, e)
        return None


def _extract_playlist_id(url: str) -> str | None:
    """Return the playlist ID from a youtube.com/playlist?list=... URL, or None."""
    try:
        from urllib.parse import parse_qs
        qs = parse_qs(urlparse(url).query)
        ids = qs.get("list", [])
        return ids[0] if ids else None
    except Exception:
        return None


async def _first_video_from_playlist(playlist_id: str, api_key: str):
    """Fetch the first video from a YouTube playlist (1 quota unit)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={"part": "snippet", "playlistId": playlist_id, "maxResults": 1, "key": api_key},
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                return None
            snippet = items[0]["snippet"]
            vid = snippet["resourceId"]["videoId"]
            title = snippet.get("title", "")
            description = (snippet.get("description") or "")[:300]
            return {"url": f"https://www.youtube.com/watch?v={vid}", "title": title, "description": description}
    except Exception as e:
        logger.warning("Playlist resolution failed (id=%s): %s", playlist_id, e)
        return None


async def resolve_youtube_channel_to_video(link: dict) -> dict:
    """
    If `link` is a YouTube channel or playlist URL, attempt to resolve it to
    the most recent video using the YouTube Data API.

    Returns the original link unchanged if:
    - it's already a video URL (/watch?v=...)
    - no YOUTUBE_API_KEY is configured
    - the API call fails for any reason
    """
    url = link.get("url", "")
    if "youtube.com" not in url and "youtu.be" not in url:
        return link

    # Handle playlist URLs
    playlist_id = _extract_playlist_id(url)
    if playlist_id and "watch" not in url:
        if not YOUTUBE_API_KEY:
            return link
        resolved = await _first_video_from_playlist(playlist_id, YOUTUBE_API_KEY)
        if resolved:
            updated = link.copy()
            updated["url"] = resolved["url"]
            if resolved.get("title"):
                updated["title"] = resolved["title"]
            if resolved.get("description") is not None:
                updated["description"] = resolved["description"]
            logger.info("Resolved playlist %s → %s", url, resolved["url"])
            return updated
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
