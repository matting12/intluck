import httpx
import logging

from app.utils.social_utils import is_social_media_url

logger = logging.getLogger(__name__)

async def brave_search(query: str, api_key: str, category: str = None):
    """
    Performs a Brave search and returns results.
    
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

    params = {"q": query, "count": 5}

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
