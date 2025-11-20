import tldextract

def shorten_title(title: str) -> str:
    """Extracts a clean short title using common separators."""
    if not title:
        return ""

    separators = [" | ", " - ", " — ", " · ", " » ", ": "]
    for sep in separators:
        if sep in title:
            return title.split(sep)[0].strip()

    return title.strip()

def infer_site_name(url: str) -> str:
    """
    Convert a domain like 'mcgovern.org' into a site name like 'McGovern'.
    More advanced: If the domain contains multiple tokens, convert to proper title case.
    """
    try:
        ext = tldextract.extract(url)
        domain = ext.domain
        suffix = ext.suffix  # for future use

        # Expand well-known sites (optional, extendable)
        known = {
            "nytimes": "New York Times",
            "wsj": "Wall Street Journal",
            "github": "GitHub",
            "linkedin": "LinkedIn",
            "openai": "OpenAI"
        }
        if domain in known:
            return known[domain]

        # Default: Title-case the domain
        return domain.replace("-", " ").title()

    except Exception:
        return "Unknown"
