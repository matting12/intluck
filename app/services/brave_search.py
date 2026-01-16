import httpx
import logging
from urllib.parse import urlparse

from app.utils.social_utils import is_social_media_url

logger = logging.getLogger(__name__)

# Non-English top-level domains to filter out
NON_ENGLISH_TLDS = {
    '.cn', '.ru', '.jp', '.kr', '.tw', '.hk', '.th', '.vn', '.id',
    '.my', '.sg', '.ph', '.in', '.pk', '.bd', '.ir', '.sa', '.ae',
    '.eg', '.tr', '.pl', '.cz', '.hu', '.ro', '.bg', '.ua', '.by',
    '.gr', '.il', '.br', '.mx', '.ar', '.cl', '.co', '.pe', '.ve',
    '.es', '.pt', '.fr', '.de', '.it', '.nl', '.be', '.at', '.ch',
    '.se', '.no', '.dk', '.fi'
}

# Country code subdomains/paths that indicate non-English content
NON_ENGLISH_INDICATORS = {
    '/zh/', '/ja/', '/ko/', '/ru/', '/de/', '/fr/', '/es/', '/pt/',
    '/it/', '/nl/', '/pl/', '/tr/', '/ar/', '/hi/', '/th/', '/vi/',
    '.cn/', '.jp/', '.kr/', '.ru/', '.de/', '.fr/', '.es/', '.br/',
    'zh-cn', 'zh-tw', 'ja-jp', 'ko-kr', 'ru-ru', 'de-de', 'fr-fr',
}


def is_english_domain(url: str) -> bool:
    """
    Check if a URL is likely to be English content.

    Args:
        url: The URL to check

    Returns:
        True if the URL appears to be English content
    """
    url_lower = url.lower()

    # Check for non-English TLDs
    try:
        parsed = urlparse(url_lower)
        domain = parsed.netloc

        # Check TLD
        for tld in NON_ENGLISH_TLDS:
            if domain.endswith(tld):
                return False

        # Check for country-specific subdomains
        for indicator in NON_ENGLISH_INDICATORS:
            if indicator in url_lower:
                return False

    except Exception:
        pass

    return True


async def brave_search(query: str, api_key: str, category: str = None):
    """
    Performs a Brave search and returns results.
    Filters to English-only content from English-speaking domains.

    Args:
        query: Search query string
        api_key: Brave API key
        category: Optional category hint (e.g., "social" to filter social media URLs)

    Returns:
        List of dicts with url, title, description keys
    """
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }

    # Enhanced parameters for English-only results
    params = {
        "q": query,
        "count": 20,
        "search_lang": "en",      # Search language
        "ui_lang": "en-US",       # UI language
        "country": "us",          # Country preference
        "result_filter": "web"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            web_results = data.get("web", {}).get("results", [])
            output = []

            for r in web_results:
                url = r.get("url", "")

                # Filter out non-English domains
                if not is_english_domain(url):
                    logger.debug(f"Filtered non-English URL: {url}")
                    continue

                # If category is "social", only include social media URLs
                if category == "social" and not is_social_media_url(url):
                    continue

                output.append({
                    "url": url,
                    "title": r.get("title", ""),
                    "description": r.get("description", "")
                })

            return output

    except Exception as e:
        logger.error(f"Brave search error [{category}]: {e}")
        raise


async def brave_search_videos(query: str, api_key: str, count: int = 3):
    """
    Performs a Brave video search and returns embeddable video results.
    Filters to English-only content.

    Args:
        query: Search query string
        api_key: Brave API key
        count: Number of videos to return (default 3)

    Returns:
        List of dicts with url, title, description, type='video' keys
        Filtered to only YouTube/Vimeo URLs for embeddability
    """
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }

    # Enhanced parameters for English-only video results
    params = {
        "q": query,
        "count": count * 2,  # Request more to account for filtering
        "country": "us",
        "search_lang": "en",
        "ui_lang": "en-US"
    }

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Searching videos: {query}")

            response = await client.get(
                "https://api.search.brave.com/res/v1/videos/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            video_results = data.get("results", [])
            output = []

            for r in video_results:
                url = r.get("url", "")

                # Only include YouTube and Vimeo (embeddable platforms)
                if not ("youtube.com" in url or "youtu.be" in url or "vimeo.com" in url):
                    continue

                # Filter out non-English video URLs
                if not is_english_domain(url):
                    continue

                output.append({
                    "url": url,
                    "title": r.get("title", ""),
                    "description": r.get("description", ""),
                    "type": "video"  # Flag for frontend detection
                })

                # Stop once we have enough
                if len(output) >= count:
                    break

            logger.info(f"Found {len(output)} embeddable videos (filtered from {len(video_results)} total)")
            return output

    except Exception as e:
        logger.error(f"Brave video search error: {e}")
        # Return empty list on error (graceful degradation)
        return []
