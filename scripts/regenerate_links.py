#!/usr/bin/env python3
"""
Regenerate full-links-results.json by calling the company-info API for all companies.
Run this script with the server running on the specified port.

Usage:
    python scripts/regenerate_links.py --port 8000
    python scripts/regenerate_links.py --port 8001 --resume
"""

import argparse
import json
import time
import sys
from datetime import datetime
from pathlib import Path

import requests

# Files
DATA_DIR = Path(__file__).parent.parent / "data"
NOTES_DIR = Path(__file__).parent.parent / "notes"
COMPANIES_FILE = DATA_DIR / "top_companies.json"
OUTPUT_FILE = NOTES_DIR / "full-links-results.json"

YOUTUBE_THRESHOLD = 85


def load_companies() -> list:
    """Load company list from JSON file."""
    with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_existing_results() -> dict:
    """Load existing results for resume functionality."""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"companies": {}}


def get_company_info(company: str, port: int, timeout: int = 30) -> dict:
    """Call the company-info API endpoint."""
    url = f"http://127.0.0.1:{port}/api/company-info"
    params = {
        "company": company,
        "job_title": "Software Engineer",  # Default job title for link generation
        "no_cache": "true"  # Skip cache to get fresh results
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)[:50]}


def save_results(results: dict):
    """Save results to JSON file."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Regenerate full-links-results.json")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing results")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    args = parser.parse_args()

    # Load companies
    companies = load_companies()
    total = len(companies)
    print(f"Loaded {total} companies from {COMPANIES_FILE}")

    # Check server is running
    try:
        requests.get(f"http://127.0.0.1:{args.port}/api/status", timeout=5)
        print(f"Server is running on port {args.port}")
    except:
        print(f"ERROR: Server not running on port {args.port}")
        print(f"Start the server first: uvicorn app.main:app --port {args.port}")
        sys.exit(1)

    # Load existing results if resuming
    if args.resume:
        results = load_existing_results()
        existing = set(results.get("companies", {}).keys())
        print(f"Resuming with {len(existing)} existing results")
    else:
        results = {
            "started_at": datetime.now().isoformat(),
            "total_companies": total,
            "youtube_threshold": YOUTUBE_THRESHOLD,
            "companies": {}
        }
        existing = set()

    # Process each company
    start_time = time.time()
    success_count = 0
    error_count = 0

    for i, company in enumerate(companies, 1):
        # Skip if already processed (resume mode)
        if company in existing:
            result = results["companies"][company]
            if "error" not in result:
                success_count += 1
            else:
                error_count += 1
            continue

        # Get company info (handle unicode in company names)
        safe_name = company.encode('ascii', 'replace').decode('ascii')
        print(f"[{i}/{total}] {safe_name}...", end=" ", flush=True)
        data = get_company_info(company, args.port, args.timeout)

        if "error" in data:
            print(f"ERROR: {data['error']}")
            results["companies"][company] = {"error": data["error"]}
            error_count += 1
        else:
            link_count = len(data.get("links", []))
            domain = data.get("domain")
            results["companies"][company] = {
                "domain": domain,
                "link_count": link_count,
                "links": data.get("links", [])
            }
            print(f"OK ({link_count} links, domain: {domain})")
            success_count += 1

        # Save periodically (every 10 companies)
        if i % 10 == 0:
            save_results(results)

        # Rate limiting - small delay to avoid hammering
        time.sleep(0.1)

    # Final save
    results["completed_at"] = datetime.now().isoformat()
    results["summary"] = {
        "total": total,
        "success": success_count,
        "errors": error_count
    }
    save_results(results)

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f}s")
    print(f"Success: {success_count}, Errors: {error_count}")
    print(f"Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
