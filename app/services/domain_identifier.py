import httpx
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

async def identify_company_domain(company: str, api_key: str) -> str:
    query = f"{company} official website"

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }

    print(query)
    params = {"q": query, "count": 10}  # Get more results to analyze

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
            results = data.get("web", {}).get("results", [])

            if not results:
                return ""

            # Filter out common non-company domains
            excluded_domains = {
                'wikipedia.org', 'linkedin.com', 'facebook.com', 
                'twitter.com', 'instagram.com', 'youtube.com',
                'crunchbase.com', 'bloomberg.com', 'reuters.com',
                'forbes.com', 'indeed.com', 'glassdoor.com',
                'yelp.com', 'bbb.org', 'reddit.com'
            }
            
            # Score each domain based on signals
            domain_scores = {}
            
            for result in results[:10]:
                url = result.get("url", "")
                title = result.get("title", "").lower()
                description = result.get("description", "").lower()
                
                parsed = urlparse(url)
                domain = parsed.netloc.replace("www.", "")
                
                # Skip excluded domains
                if any(excluded in domain for excluded in excluded_domains):
                    continue
                
                # Skip subdomains that look like documentation/support
                if any(subdomain in parsed.netloc for subdomain in ['docs.', 'support.', 'help.', 'blog.', 'dev.', 'developers.']):
                    continue
                
                # Initialize score for this domain
                if domain not in domain_scores:
                    domain_scores[domain] = 0
                
                # Scoring heuristics
                company_lower = company.lower()
                
                # Strong signals (higher weight)
                if company_lower in domain:
                    domain_scores[domain] += 10
                
                if any(keyword in title for keyword in ['official', 'home', company_lower]):
                    domain_scores[domain] += 5
                
                # Root domain (not a deep path) is a good signal
                if parsed.path in ['/', '']:
                    domain_scores[domain] += 3
                
                # Earlier results get higher scores
                domain_scores[domain] += (10 - results.index(result)) * 0.5
                
                # Description mentions official/homepage
                if any(keyword in description for keyword in ['official', 'homepage', 'welcome to']):
                    domain_scores[domain] += 2
            
            # Return highest scoring domain
            if domain_scores:
                best_domain = max(domain_scores, key=domain_scores.get)
                return best_domain
            
            # Fallback: return first non-excluded domain
            for result in results:
                parsed = urlparse(result.get("url", ""))
                domain = parsed.netloc.replace("www.", "")
                if not any(excluded in domain for excluded in excluded_domains):
                    return domain
            
            return ""

    except Exception as e:
        logger.error(f"Domain identification error: {e}")
        return ""
