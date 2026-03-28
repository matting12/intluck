#!/usr/bin/env python3
"""
Parse full-links-log.txt to extract valid company data and create full-links-results.json.
This recovers data from an incomplete run.
"""

import json
import re
from datetime import datetime
from pathlib import Path

NOTES_DIR = Path(__file__).parent.parent / "notes"
LOG_FILE = NOTES_DIR / "full-links-log.txt"
OUTPUT_FILE = NOTES_DIR / "full-links-results.json"

YOUTUBE_THRESHOLD = 85


def parse_log():
    """Parse the log file and extract company data."""

    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    results = {
        "started_at": datetime.now().isoformat(),
        "youtube_threshold": YOUTUBE_THRESHOLD,
        "companies": {}
    }

    # Pattern to match company entries
    # [1/1648] Company Name
    #   Domain: domain.com
    #   Links (N):
    #     - [Category] Title
    #       URL: https://...
    #       Score: NN

    company_pattern = re.compile(
        r'\[(\d+)/\d+\]\s+(.+?)\n'
        r'(?:  Domain:\s*(.+?)\n)?'
        r'(?:  Links \((\d+)\):)?',
        re.MULTILINE
    )

    # Find all companies
    current_pos = 0
    success_count = 0
    error_count = 0

    for match in company_pattern.finditer(content):
        num = int(match.group(1))
        company_name = match.group(2).strip()

        # Check if it's an error
        if "ERROR" in company_name:
            company_name = company_name.split(":")[0].strip()
            results["companies"][company_name] = {"error": "HTTP connection error"}
            error_count += 1
            continue

        domain = match.group(3).strip() if match.group(3) else None
        if domain == "None":
            domain = None

        link_count = int(match.group(4)) if match.group(4) else 0

        # Now extract the links for this company
        start_pos = match.end()

        # Find the next company entry
        next_match = company_pattern.search(content, start_pos)
        if next_match:
            section = content[start_pos:next_match.start()]
        else:
            section = content[start_pos:]

        # Parse links from section
        links = []
        link_pattern = re.compile(
            r'-\s+\[(.+?)\]\s+(.+?)\n'
            r'\s+URL:\s+(.+?)\n'
            r'\s+Score:\s+(\d+)',
            re.MULTILINE
        )

        for link_match in link_pattern.finditer(section):
            category = link_match.group(1).strip()
            title = link_match.group(2).strip()
            url = link_match.group(3).strip()
            score = int(link_match.group(4))

            links.append({
                "category": category,
                "title": title,
                "url": url,
                "score": score
            })

        results["companies"][company_name] = {
            "domain": domain,
            "link_count": len(links),
            "links": links
        }
        success_count += 1
        print(f"[{num}] {company_name}: {len(links)} links")

    results["completed_at"] = datetime.now().isoformat()
    results["total_companies"] = len(results["companies"])
    results["summary"] = {
        "parsed_success": success_count,
        "parsed_errors": error_count
    }

    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nParsed {success_count} companies with valid data")
    print(f"Found {error_count} companies with errors")
    print(f"Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    parse_log()
