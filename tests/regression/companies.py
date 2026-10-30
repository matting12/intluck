"""Regression company set. Why each company is here: docs/TEST_COMPANIES.md."""

JOB_TITLES = {
    'public': 'Software Engineer',
    'private': 'Software Engineer',
    'law': 'Associate Attorney',
    'defense': 'Systems Engineer',
    'past_bugs': 'Software Engineer',
}

COMPANIES = {
    'public': ['Walmart', 'Amazon', 'UnitedHealth Group', 'Apple', 'CVS Health', 'Berkshire Hathaway',
               'Alphabet', 'Exxon Mobil', 'McKesson', 'Cencora'],
    'private': ['Cargill', 'Koch', 'Publix Super Markets', 'Mars', 'H-E-B Grocery Company', 'Reyes Holdings',
                'Enterprise Mobility', 'Fidelity Investments', "Southern Glazer's Wine & Spirits", 'Cox Enterprises'],
    'law': ['Kirkland & Ellis', 'Latham & Watkins', 'Skadden Arps Slate Meagher & Flom', 'Sidley Austin',
            'Gibson Dunn & Crutcher', 'Morgan Lewis & Bockius', 'White & Case', 'Ropes & Gray', 'Jones Day',
            'Paul Weiss Rifkind Wharton & Garrison'],
    'defense': ['Lockheed Martin', 'RTX', 'Northrop Grumman', 'General Dynamics', 'The Boeing Company',
                'L3Harris Technologies', 'Leidos', 'HII', 'Amentum', 'Booz Allen Hamilton'],
    # Companies that broke in production before — keep them covered
    'past_bugs': ['Delta Air Lines'],
}

ALL = [(name, group) for group, names in COMPANIES.items() for name in names]
