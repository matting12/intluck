__all__ = ['infer_job_family', 'JOB_FAMILIES']

JOB_FAMILIES = {
    "Technology & Engineering": [
        "software", "engineer", "developer", "programmer", "devops", "sre",
        "frontend", "backend", "fullstack", "full-stack", "full stack",
        "data engineer", "platform", "infrastructure", "cloud", "architect",
        "security engineer", "qa", "quality assurance", "test engineer",
        "mobile developer", "ios", "android", "web developer", "embedded",
        "machine learning", "ml engineer", "ai engineer", "systems engineer"
    ],
    
    "Finance & Accounting": [
        "accountant", "accounting", "cpa", "auditor", "bookkeeper",
        "financial analyst", "finance manager", "controller", "cfo",
        "tax", "treasury", "accounts payable", "accounts receivable",
        "budget", "payroll", "billing", "revenue", "fiscal"
    ],
    
    "Healthcare & Medical": [
        "nurse", "rn", "lpn", "cna", "physician", "doctor", "md",
        "pharmacist", "therapist", "technician", "medical assistant",
        "healthcare", "clinical", "patient care", "emt", "paramedic",
        "surgeon", "dentist", "optometrist", "psychiatrist", "psychologist",
        "radiologist", "sonographer", "phlebotomist", "caregiver"
    ],
    
    "Sales & Marketing": [
        "sales", "account executive", "account manager", "sdr", "bdr",
        "business development", "marketing", "brand", "content",
        "social media", "seo", "sem", "growth", "demand gen",
        "product marketing", "communications", "pr", "public relations",
        "advertising", "copywriter", "campaign", "digital marketing"
    ],
    
    "Operations & Supply Chain": [
        "operations", "supply chain", "logistics", "warehouse",
        "inventory", "procurement", "purchasing", "buyer",
        "fulfillment", "distribution", "shipping", "receiving",
        "fleet", "transportation", "import", "export", "customs"
    ],
    
    "Legal": [
        "attorney", "lawyer", "paralegal", "legal assistant", "counsel",
        "litigation", "corporate counsel", "contract", "compliance",
        "regulatory", "legal secretary", "law clerk", "juris"
    ],
    
    "Human Resources": [
        "human resources", "hr ", "recruiter", "recruiting", "talent",
        "people operations", "hrbp", "compensation", "benefits",
        "employee relations", "training", "learning and development",
        "onboarding", "staffing"
    ],
    
    "Customer Service & Support": [
        "customer service", "customer support", "call center",
        "client services", "help desk", "support specialist",
        "customer success", "client success", "technical support",
        "customer experience", "cx "
    ],
    
    "Data & Analytics": [
        "data scientist", "data analyst", "analytics", "bi ",
        "business intelligence", "statistician", "quantitative",
        "data visualization", "tableau", "power bi"
    ],
    
    "Product Management": [
        "product manager", "product owner", "program manager",
        "project manager", "pmo", "scrum master", "agile coach"
    ],
    
    "Design & Creative": [
        "designer", "ux", "ui", "user experience", "user interface",
        "graphic design", "visual design", "creative director",
        "art director", "illustrator", "animator", "video editor",
        "photographer", "brand designer", "product designer"
    ],
    
    "Education & Training": [
        "teacher", "professor", "instructor", "educator", "tutor",
        "curriculum", "academic", "principal", "dean", "admissions",
        "school", "faculty", "teaching assistant", "librarian"
    ],
    
    "Consulting": [
        "consultant", "consulting", "advisory", "advisor",
        "management consultant", "strategy consultant"
    ],
    
    "Retail & Hospitality": [
        "retail", "store manager", "cashier", "sales associate",
        "merchandiser", "barista", "server", "bartender", "host",
        "front desk", "concierge", "hotel", "restaurant", "food service"
    ],
    
    "Manufacturing & Engineering": [
        "manufacturing", "production", "assembly", "machinist",
        "welder", "fabricator", "quality control", "plant manager",
        "maintenance technician", "industrial engineer", "process engineer"
    ],
    
    "Research & Science": [
        "researcher", "scientist", "laboratory", "lab tech",
        "research associate", "principal investigator", "postdoc",
        "biologist", "chemist", "physicist", "geologist"
    ],
    
    "Real Estate & Property": [
        "real estate", "property manager", "leasing", "realtor",
        "broker", "appraiser", "escrow", "title", "mortgage"
    ],
    
    "Media & Entertainment": [
        "producer", "editor", "journalist", "reporter", "writer",
        "content creator", "broadcaster", "anchor", "director",
        "cinematographer", "sound engineer", "talent"
    ],
    
    "Non-Profit & Government": [
        "program coordinator", "grant", "fundraising", "development officer",
        "policy", "public affairs", "government", "civil servant",
        "social worker", "case manager", "community"
    ],
    
    "Transportation & Logistics": [
        "driver", "cdl", "trucker", "delivery", "courier",
        "dispatcher", "pilot", "flight attendant", "conductor"
    ]
}


def normalize_title(job_title: str) -> str:
    """Lowercase and strip whitespace"""
    return job_title.lower().strip()


def infer_job_family(job_title: str) -> str:
    """
    Match job title to a job family based on keywords.
    
    Args:
        job_title: Raw job title string
    
    Returns:
        Job family string, or "General" if no match
    """
    normalized = normalize_title(job_title)
    
    for family, keywords in JOB_FAMILIES.items():
        for keyword in keywords:
            if keyword in normalized:
                return family
    
    return "General"