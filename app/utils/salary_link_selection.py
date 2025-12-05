"""
Link selection and ordering for salary & benefits.
Similar to company_link_selection but for compensation data.
"""

__all__ = [
    'select_top_salary_link_per_category',
    'order_salary_by_priority'
]

from app.utils.salary_queries import format_salary_category_name


def select_top_salary_link_per_category(search_results: dict) -> dict:
    """
    For each category, select the top Brave search result.
    
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
            top_link['category'] = format_salary_category_name(category)
            top_link['category_key'] = category
            
            categorized[category] = top_link
    
    return categorized


def order_salary_by_priority(categorized_links: dict) -> list:
    """
    Return links in spec-defined priority order.
    
    Priority order from spec:
    1. Benefits landing page
    2. Perks
    3. ERG groups
    4. Salary
    5. Equity/Stock
    6. Health insurance reviews
    7. Insurance cost
    8. Retirement/401K
    9. Pay increases
    10. Benefits comparison
    """
    
    priority_order = [
        'benefits_landing',
        'perks',
        'erg_groups',
        'salary',
        'equity',
        'health_insurance',
        'insurance_cost',
        'retirement_401k',
        'pay_increases',
        'benefits_comparison'
    ]
    
    ordered = []
    for category in priority_order:
        if category in categorized_links:
            ordered.append(categorized_links[category])
    
    return ordered