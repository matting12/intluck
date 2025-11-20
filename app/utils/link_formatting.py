def format_link_for_display(link: dict) -> dict:
    """
    Ensures link title has format: "Page Title | Site Name"
    Only adds site name if not already present in the title.
    """
    from app.utils.url_parsing import infer_site_name
    
    title = link.get("title", "")
    url = link.get("url", "")
    
    # If title already has a pipe separator, assume it's already formatted
    if " | " in title:
        return link
    
    # If title is empty, use site name only
    if not title:
        site_name = infer_site_name(url)
        return {
            **link,
            "title": site_name
        }
    
    # Add site name to title
    site_name = infer_site_name(url)
    formatted_title = f"{title} | {site_name}"
    
    return {
        **link,
        "title": formatted_title
    }