"""
Job family-specific query templates for company-specific interview prep.
Each family has queries designed to find company tools, processes, and real interview data.
"""

def get_interview_prep_queries(company: str, job_title: str, job_family: str) -> list[str]:
    """
    Generate 3-4 targeted queries based on job family.
    Focus on: company tools, business metrics, real interviews, role-specific intel
    
    Args:
        company: Company name (e.g., "Microsoft", "Burlington")
        job_title: Job title (e.g., "Software Engineer", "Accountant")
        job_family: Job family category (e.g., "Technology & Engineering")
    
    Returns:
        List of 3-4 search query strings optimized for that job family
    """
    
    query_templates = {
        "Technology & Engineering": [
            f"{company} tech stack",
            f"{company} engineering blog OR architecture OR infrastructure",
            f"{company} {job_title} interview experience site:levels.fyi OR site:glassdoor.com OR site:leetcode.com",
            f"{company} github OR open source OR developer resources"
        ],
        
        "Finance & Accounting": [
            f"{company} quarterly earnings OR 10-K OR 10-Q OR financial results",
            f"{company} accounting software OR ERP system OR financial platform OR SAP OR Oracle OR NetSuite",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} financial performance OR revenue OR balance sheet OR SEC filings"
        ],
        
        "Healthcare & Medical": [
            f"{company} EMR system OR electronic health records OR Epic OR Cerner",
            f"{company} patient care protocols OR clinical guidelines OR treatment standards",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} hospital ranking OR patient outcomes OR quality metrics OR safety scores"
        ],
        
        "Sales & Marketing": [
            f"{company} CRM system OR Salesforce OR HubSpot OR sales tools",
            f"{company} marketing stack OR martech OR analytics platform OR Tableau OR Google Analytics",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:repvue.com OR site:indeed.com",
            f"{company} go-to-market strategy OR sales process OR customer acquisition"
        ],
        
        "Operations & Supply Chain": [
            f"{company} supply chain management OR logistics platform OR warehouse system",
            f"{company} inventory management OR fulfillment OR distribution centers",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} operations OR efficiency OR process improvement OR lean"
        ],
        
        "Legal": [
            f"{company} legal department OR general counsel OR legal team structure",
            f"{company} practice management software OR legal tech OR case management",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:vault.com OR site:indeed.com",
            f"{company} litigation OR regulatory OR compliance issues OR legal news"
        ],
        
        "Human Resources": [
            f"{company} HRIS system OR Workday OR ADP OR BambooHR OR HR platform",
            f"{company} employee benefits OR compensation philosophy OR total rewards",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} culture OR employee engagement OR DEI initiatives OR workplace"
        ],
        
        "Customer Service & Support": [
            f"{company} customer support platform OR Zendesk OR Salesforce Service Cloud OR help desk",
            f"{company} customer satisfaction OR NPS OR support metrics OR service quality",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} support process OR ticket system OR customer experience"
        ],
        
        "Data & Analytics": [
            f"{company} data infrastructure OR data warehouse OR cloud platform OR Snowflake OR Databricks",
            f"{company} analytics tools OR BI platform OR Tableau OR Power BI OR Looker",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:levels.fyi",
            f"{company} data science OR machine learning OR AI initiatives OR data strategy"
        ],
        
        "Product Management": [
            f"{company} product roadmap OR product strategy OR product vision",
            f"{company} product management tools OR JIRA OR Aha OR ProductBoard OR roadmap",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:levels.fyi",
            f"{company} product launches OR feature releases OR product updates"
        ],
        
        "Design & Creative": [
            f"{company} design system OR design language OR brand guidelines",
            f"{company} design tools OR Figma OR Sketch OR Adobe OR creative software",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} design process OR UX research OR design thinking OR creative workflow"
        ],
        
        "Education & Training": [
            f"{company} curriculum OR teaching methods OR educational approach",
            f"{company} learning management system OR LMS OR educational technology",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} student outcomes OR academic performance OR accreditation"
        ],
        
        "Consulting": [
            f"{company} consulting methodology OR framework OR approach",
            f"{company} case study OR client success OR project examples",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:vault.com OR site:managementconsulted.com",
            f"{company} practice areas OR industry expertise OR service offerings"
        ],
        
        "Retail & Hospitality": [
            f"{company} point of sale system OR POS OR inventory management",
            f"{company} customer service OR guest experience OR service standards",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} store operations OR employee training OR retail technology"
        ],
        
        "Manufacturing & Engineering": [
            f"{company} manufacturing process OR production system OR quality control",
            f"{company} equipment OR machinery OR manufacturing technology OR automation",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} safety standards OR lean manufacturing OR continuous improvement"
        ],
        
        "Research & Science": [
            f"{company} research areas OR laboratories OR scientific focus",
            f"{company} research tools OR equipment OR laboratory systems",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} publications OR research output OR scientific contributions"
        ],
        
        "Real Estate & Property": [
            f"{company} property management software OR real estate platform",
            f"{company} portfolio OR properties OR real estate holdings",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} market analysis OR property valuation OR investment strategy"
        ],
        
        "Media & Entertainment": [
            f"{company} content management system OR production tools OR media technology",
            f"{company} content strategy OR programming OR media offerings",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} audience OR viewership OR ratings OR content performance"
        ],
        
        "Non-Profit & Government": [
            f"{company} mission OR programs OR services OR initiatives",
            f"{company} funding OR grants OR budget OR financial reporting",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} impact OR outcomes OR program effectiveness OR community"
        ],
        
        "Transportation & Logistics": [
            f"{company} fleet management OR transportation system OR logistics platform",
            f"{company} routing OR dispatch OR delivery operations",
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} safety OR compliance OR operational efficiency"
        ]
    }
    
    # Get queries for this job family, or fall back to generic
    if job_family in query_templates:
        return query_templates[job_family]
    else:
        # Generic fallback for unknown job families
        return [
            f"{company} {job_title} interview experience site:glassdoor.com OR site:indeed.com",
            f"{company} tools and platforms for {job_title}",
            f"{company} {job_title} interview questions",
            f"{company} work environment OR culture for {job_title}"
        ]


def get_company_info_queries(company: str) -> list[str]:
    """
    Generate queries for company information section.
    Focus on: official company sources, leadership, culture, social presence
    """
    return [
        f"{company} about OR company overview site:linkedin.com OR site:crunchbase.com",
        f"{company} leadership OR executives OR management team",
        f"{company} culture OR values OR mission OR careers",
        f"{company} news OR press releases OR announcements"
    ]


def get_salary_queries(company: str, job_title: str, location: str) -> list[str]:
    """
    Generate queries for salary and benefits section.
    Focus on: compensation data, benefits, work-life balance
    
    Args:
        location: City, State format (e.g., "Seattle, WA")
    """
    return [
        f"{company} {job_title} salary {location} site:levels.fyi OR site:glassdoor.com",
        f"{company} {job_title} compensation site:levels.fyi OR site:payscale.com",
        f"{company} benefits OR perks OR employee benefits",
        f"{company} work life balance OR remote work OR flexible schedule"
    ]


def get_reviews_queries(company: str) -> list[str]:
    """
    Generate queries for company reviews section.
    Focus on: employee reviews, culture insights, career development
    """
    return [
        f"{company} employee reviews site:glassdoor.com OR site:indeed.com OR site:comparably.com",
        f"{company} culture OR workplace OR employee experience",
        f"{company} career development OR growth opportunities OR promotions",
        f"{company} management OR leadership reviews"
    ]