"""
Link selection and ordering for company overview.
Replaces GPT selection with category-based approach.
"""

__all__ = [
    'select_top_link_per_category',
    'order_by_priority'
]

from app.utils.company_queries import format_category_name


def select_top_link_per_category(search_results: dict) -> dict:
    """
    For each category, select the top Brave search result.
    No GPT needed - Brave ranking + site:{domain} filter provides quality.
    
    Args:
        search_results: {category: [list of link dicts]}
    
    Returns:
        {category: single_link_dict}
    """
    
    categorized = {}
    
    for category, links in search_results.items():
        if links and len(links) > 0:
            # Take first result from Brave
            top_link = links[0].copy()
            
            # Add formatted category name
            top_link['category'] = format_category_name(category)
            top_link['category_key'] = category
            
            categorized[category] = top_link
    
    return categorized


def order_by_priority(categorized_links: dict) -> list:
    """
    Return links in spec-defined priority order.
    
    Priority order from spec:
    1. About Us
    2. Mission/Vision Statement
    3. Company Culture
    4. Department/Leadership
    5. Social Media
    6. History
    7. Community Engagement
    8. Financial Reports
    9. News
    """
    
    priority_order = [
        'about_us',
        'mission_vision',
        'culture',
        'department',
        'social_media',
        'history',
        'community',
        'financials',
        'news'
    ]
    
    ordered = []
    for category in priority_order:
        if category in categorized_links:
            ordered.append(categorized_links[category])
    
    return ordered