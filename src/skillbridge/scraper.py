"""Web scraping functionality for Skillbridge opportunities."""

import re
from playwright.sync_api import sync_playwright
from typing import List, Optional, Dict, Any, Tuple

from .config import (
    TABLE_WRAPPER_SELECTOR,
    ROW_SELECTOR,
    SEARCH_INPUT_SELECTOR,
    SEARCH_BUTTON_SELECTOR,
    NEXT_PAGE_SELECTOR,
    TOTAL_PAGES_SELECTOR,
    PAGE_LOAD_DELAY,
)
from .schema import SkillbridgeOpportunity

def extract_coordinates(html: str) -> Optional[Tuple[float, float]]:
    """Extracts latitude and longitude from the onclick attribute."""
    match = re.search(r"ShowPin\((-?\d+\.\d+),(-?\d+\.\d+),", html)
    if match:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        return latitude, longitude
    return None

def extract_opportunity_data(row) -> Optional[SkillbridgeOpportunity]:
    """Extracts and validates opportunity data from a table row."""
    cells = row.query_selector_all("td")
    if not cells:
        return None

    data = {}
    
    # Extract data using schema field definitions
    for field in SkillbridgeOpportunity.__fields__.values():
        if hasattr(field, 'column_index') and field.column_index is not None:
            if len(cells) > field.column_index:
                data[field.name] = cells[field.column_index].inner_text()

    # Handle coordinates separately since they require special extraction
    if cells:
        coordinates = extract_coordinates(cells[0].inner_html())
        if coordinates:
            data["latitude"] = coordinates[0]
            data["longitude"] = coordinates[1]

    try:
        return SkillbridgeOpportunity(**data)
    except ValueError as e:
        print(f"Error validating data: {e}")
        return None

def scrape_search_results(url: str, search_query: str) -> List[Dict[str, Any]]:
    """Scrapes search results from a given URL and search query."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        # Perform search
        page.fill(SEARCH_INPUT_SELECTOR, search_query)
        page.click(SEARCH_BUTTON_SELECTOR)
        page.wait_for_selector(TABLE_WRAPPER_SELECTOR)

        opportunities = []
        total_pages_element = page.query_selector(TOTAL_PAGES_SELECTOR)
        total_pages = int(total_pages_element.inner_text()) if total_pages_element else 1

        # Iterate through pages and extract data
        for _ in range(total_pages):
            rows = page.query_selector_all(ROW_SELECTOR)
            for row in rows:
                opportunity = extract_opportunity_data(row)
                if opportunity:
                    # Convert Pydantic model to dict for storage
                    opportunities.append(opportunity.model_dump(exclude_unset=True))

            # Navigate to next page if available
            next_page_button = page.query_selector(NEXT_PAGE_SELECTOR)
            if next_page_button:
                next_page_button.click()
                page.wait_for_timeout(PAGE_LOAD_DELAY)
            else:
                break

        browser.close()
        return opportunities
