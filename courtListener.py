#!/usr/bin/env python3
# Authored by Michael Mendy

import argparse
import requests
import sys
import csv
import os
from typing import Union, Dict, Optional, List
from datetime import datetime
from rich.console import Console
from rich.table import Table

API_BASE = "https://www.courtlistener.com/api/rest/v4"
API_TOKEN = "" # your CourtListener or Thomson Reuters API token here.

HEADERS = {
    "User-Agent": "CourtListenerCLI/1.5 (Michael Mendy <craftykisses@gmail.com>)",
    "Authorization": f"Token {API_TOKEN}",
}

console = Console()
court_cache: Dict[str, str] = {}


def validate_date(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def resolve_court_name(court_ref: Union[str, dict]) -> str:
    """Resolve court name from a reference (URL or dict)."""
    if isinstance(court_ref, dict):
        return court_ref.get("name", "Unknown Court")

    if isinstance(court_ref, str) and court_ref.startswith("/api/"):
        if court_ref in court_cache:
            return court_cache[court_ref]

        court_url = f"https://www.courtlistener.com{court_ref}"
        try:
            response = requests.get(court_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            name = response.json().get("name", court_ref.split("/")[-2])
            court_cache[court_ref] = name
            return name
        except requests.RequestException as e:
            console.print(f"Failed to fetch court name: {e}")
            return court_ref.split("/")[-2]

    return court_ref or "Unknown Court"


def list_popular_courts() -> None:
    """Display a table of popular court slugs and their full names."""
    popular = [
        ("scotus", "Supreme Court of the United States"),
        ("ca9", "U.S. Court of Appeals for the Ninth Circuit"),
        ("ca2", "U.S. Court of Appeals for the Second Circuit"),
        ("ca5", "U.S. Court of Appeals for the Fifth Circuit"),
        ("ca1", "U.S. Court of Appeals for the First Circuit"),
        ("dc", "U.S. District Court for the District of Columbia"),
        ("nysd", "U.S. District Court for the Southern District of New York"),
        ("nyed", "U.S. District Court for the Eastern District of New York"),
        ("cand", "U.S. District Court for the Northern District of California"),
        ("cacd", "U.S. District Court for the Central District of California"),
    ]

    table = Table(title="Popular Court Slugs")
    table.add_column("Slug", style="cyan", no_wrap=True)
    table.add_column("Full Name", style="white")

    for slug, name in popular:
        table.add_row(slug, name)

    console.print(table)


def fetch_opinions(url: str, params: Dict[str, Union[str, int]]) -> List[Dict]:
    """Fetch opinions from the CourtListener API."""
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.ConnectionError:
        console.print("Connection error: Unable to reach the API.")
        sys.exit(1)
    except requests.Timeout:
        console.print("Request timed out: API took too long to respond.")
        sys.exit(1)
    except requests.HTTPError as e:
        console.print(f"HTTP error: {e.response.status_code} - {e.response.reason}")
        sys.exit(1)
    except requests.RequestException as e:
        console.print(f"API error: {e}")
        sys.exit(1)


def export_to_csv(results: List[Dict], filename: str) -> None:
    """Export opinion results to a CSV file."""
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["case_name", "court", "date_filed", "url", "docket_number", "citation"],
                extrasaction="ignore",
            )
            writer.writeheader()
            for item in results:
                court = resolve_court_name(item.get("court"))
                absolute_url = item.get("absolute_url", "")
                url = f"https://www.courtlistener.com{absolute_url}"
                writer.writerow({
                    "case_name": item.get("case_name", "Unknown Case"),
                    "court": court,
                    "date_filed": item.get("date_filed", "Unknown Date"),
                    "url": url,
                    "docket_number": item.get("docket_number", ""),
                    "citation": item.get("citation", ""),
                })
        console.print(f"Results exported to {filename}")
    except IOError as e:
        console.print(f"Error writing to CSV: {e}")
        sys.exit(1)


def display_opinions(
    results: List[Dict], query: str = "", court_slug: str = "", verbose: bool = False
) -> None:
    """Display opinion results in a formatted manner."""
    if not results:
        console.print(f"No results found for: '{query}'")
        return

    court_display = f" in {court_slug}" if court_slug else ""
    console.print(f"\nFound {len(results)} result(s) for: '{query}'{court_display}\n")

    for idx, item in enumerate(results, start=1):
        case_name = item.get("case_name", "Unknown Case")
        court = resolve_court_name(item.get("court"))
        date_filed = item.get("date_filed", "Unknown Date")
        absolute_url = item.get("absolute_url", "")
        link = f"https://www.courtlistener.com{absolute_url}"

        console.print(f"{idx}. {case_name}", style="bold cyan")
        console.print(f"   Court: {court}", style="magenta")
        console.print(f"   Date: {date_filed}", style="yellow")
        console.print(f"   {link}", style="blue underline")

        if verbose:
            docket = item.get("docket_number", "N/A")
            citation = item.get("citation", "N/A")
            console.print(f"   Docket: {docket}", style="green")
            console.print(f"   Citation: {citation}", style="green")
        console.print()


def search_opinions(
    query: str,
    max_results: int,
    court_slug: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    export_file: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Search for opinions matching the query."""
    search_url = f"{API_BASE}/search/"
    params = {
        "q": query,
        "type": "o",
        "page_size": max_results,
    }
    if court_slug:
        params["court"] = court_slug
    if start_date:
        params["date_filed__gte"] = start_date
    if end_date:
        params["date_filed__lte"] = end_date

    results = fetch_opinions(search_url, params)
    display_opinions(results, query, court_slug, verbose)
    if export_file:
        export_to_csv(results, export_file)


def fetch_current_opinions(
    max_results: int,
    court_slug: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    export_file: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Fetch opinions filed today or within a date range."""
    today = datetime.now().strftime("%Y-%m-%d")
    search_url = f"{API_BASE}/opinions/"
    params = {
        "page_size": max_results,
    }
    if court_slug:
        params["court__id"] = court_slug
    if start_date:
        params["date_filed__gte"] = start_date
    else:
        params["date_filed__gte"] = today
    if end_date:
        params["date_filed__lte"] = end_date

    results = fetch_opinions(search_url, params)
    query = f"opinions from {start_date or today} to {end_date or 'today'}"
    display_opinions(results, query, court_slug, verbose)
    if export_file:
        export_to_csv(results, export_file)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="CourtListener CLI Search Tool")
    parser.add_argument("query", nargs="?", help="Search term (e.g., 'Perkins Coie')")
    parser.add_argument("--limit", type=int, default=10, help="Max number of results to return")
    parser.add_argument("--court", type=str, help="Filter by court slug (e.g., 'scotus', 'ca9')")
    parser.add_argument("--list-courts", action="store_true", help="Print popular court slugs")
    parser.add_argument("--curr", action="store_true", help="Fetch opinions filed today")
    parser.add_argument("--start-date", type=str, help="Start date for filtering (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date for filtering (YYYY-MM-DD)")
    parser.add_argument("--export", type=str, help="Export results to a CSV file")
    parser.add_argument("--verbose", action="store_true", help="Show additional details")
    return parser.parse_args()


def main() -> None:
    """Main entry point for the CLI tool."""
    args = parse_arguments()

    if args.limit <= 0:
        console.print("Error  Error: --limit must be a positive integer")
        sys.exit(1)

    if args.start_date and not validate_date(args.start_date):
        console.print("Error: --start-date must be in YYYY-MM-DD format")
        sys.exit(1)
    if args.end_date and not validate_date(args.end_date):
        console.print("Error: --end-date must be in YYYY-MM-DD format")
        sys.exit(1)
    if args.export and not os.access(os.path.dirname(args.export) or ".", os.W_OK):
        console.print("Error: Cannot write to export file path")
        sys.exit(1)

    if args.list_courts:
        list_popular_courts()
    elif args.curr:
        fetch_current_opinions(
            args.limit,
            args.court,
            args.start_date,
            args.end_date,
            args.export,
            args.verbose,
        )
    elif args.query:
        search_opinions(
            args.query,
            args.limit,
            args.court,
            args.start_date,
            args.end_date,
            args.export,
            args.verbose,
        )
    else:
        console.print("Error: Please provide a query, use --curr, or use --list-courts")
        sys.exit(1)


if __name__ == "__main__":
    main()
