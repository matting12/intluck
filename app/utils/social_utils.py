def is_social_media_url(url: str) -> bool:
    if not url:
        return False

    url = url.lower()
    platforms = [
        "linkedin.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "facebook.com",
        "youtube.com"
    ]
    return any(p in url for p in platforms)
