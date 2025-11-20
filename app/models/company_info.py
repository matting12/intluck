class CompanyInfoResult:
    @staticmethod
    def empty(domain=None):
        return {
            "domain": domain,
            "about": [],
            "culture": [],
            "social": [],
            "executive": []
        }
