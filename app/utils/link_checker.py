"""
Async 404 checker for curated links.
Runs parallel HEAD requests and drops confirmed dead links (404/410).
Keeps links on timeout, network error, 403, or 405 — only drops hard 404s.
"""

import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

DEAD_STATUSES = {404, 410}
CHECK_TIMEOUT = 2.0  # seconds per request


async def _check_url(link: dict) -> dict | None:
    url = link.get('url', '')
    if not url:
        return None

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=CHECK_TIMEOUT) as client:
            response = await client.head(url)

            if response.status_code in DEAD_STATUSES:
                logger.info(f"[404-filter] Dropping dead link ({response.status_code}): {url[:70]}")
                return None

            # Some servers reject HEAD — retry with GET range
            if response.status_code == 405:
                response = await client.get(url, headers={'Range': 'bytes=0-0'})
                if response.status_code in DEAD_STATUSES:
                    logger.info(f"[404-filter] Dropping dead link ({response.status_code}): {url[:70]}")
                    return None

            return link

    except Exception:
        # Keep on timeout or any network error — don't punish slow sites
        return link


async def filter_dead_links(links: list[dict]) -> list[dict]:
    """
    Check all links in parallel and drop confirmed 404/410s.
    Order is preserved.
    """
    if not links:
        return []

    results = await asyncio.gather(*[_check_url(link) for link in links])
    live = [l for l in results if l is not None]

    dropped = len(links) - len(live)
    if dropped:
        logger.info(f"[404-filter] Dropped {dropped} dead link(s) from {len(links)}")

    return live
