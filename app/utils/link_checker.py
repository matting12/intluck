"""
Async 404 checker for curated links.
Runs parallel HEAD requests and drops confirmed dead links: 404/410 responses,
or a DNS/connect failure (host doesn't exist or refused the connection).
Keeps links on timeout or any other network error — only drops hard failures.
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

    except httpx.ConnectError:
        # DNS resolution failure or refused connection — the host doesn't
        # exist or isn't listening at all, unlike a slow/timing-out server.
        logger.info(f"[404-filter] Dropping dead link (connect error): {url[:70]}")
        return None

    except Exception:
        # Keep on timeout or any other network error — don't punish slow sites
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


async def _demo():
    """Self-check: a dead (no-DNS) host is dropped, a live one is kept.
    Run: python -m app.utils.link_checker (needs network access)"""
    links = [
        {'url': 'https://cgp.coca-cola.com/', 'title': 'decommissioned subdomain'},
        {'url': 'https://www.coca-cola.com/', 'title': 'live site'},
    ]
    live = await filter_dead_links(links)
    live_urls = {l['url'] for l in live}
    assert live_urls == {'https://www.coca-cola.com/'}, live_urls
    print("ok:", live_urls)


if __name__ == "__main__":
    asyncio.run(_demo())
