import re
from datetime import datetime
import json
from playwright.sync_api import sync_playwright
from typing import Optional, List
from pydantic import BaseModel

TABLE_WRAPPER_SELECTOR = "#location-table_wrapper"
ROW_SELECTOR = "#location-table > tbody > tr[role=\"row\"]"
SEARCH_INPUT_SELECTOR = "#keywords"
SEARCH_BUTTON_SELECTOR = "#loc-search-btn"
NEXT_PAGE_SELECTOR = "#location-table_next"
TOTAL_PAGES_SELECTOR = "#location-table_paginate > span > a:nth-child(5)"
PAGE_LOAD_DELAY = 500  # Milliseconds

class SkillbridgeOpportunity(BaseModel):
    partner_program_agency: Optional[str] = None
    service: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    duration_of_training: Optional[str] = None
    employer_poc: Optional[str] = None
    poc_email: Optional[str] = None
    cost: Optional[str] = None
    closest_installation: Optional[str] = None
    opportunity_locations_by_state: Optional[str] = None
    delivery_method: Optional[str] = None
    target_mocs: Optional[str] = None
    other_eligibility_factors: Optional[str] = None
    other_prerequisite: Optional[str] = None
    jobs_description: Optional[str] = None
    summary_description: Optional[str] = None
    job_family: Optional[str] = None
    mou_organization: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

def extract_coordinates(html: str) -> Optional[tuple[float, float]]:
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

    data = {
        "partner_program_agency": cells[1].inner_text() if len(cells) > 1 else None,
        "service": cells[2].inner_text() if len(cells) > 2 else None,
        "city": cells[3].inner_text() if len(cells) > 3 else None,
        "state": cells[4].inner_text() if len(cells) > 4 else None,
        "duration_of_training": cells[5].inner_text() if len(cells) > 5 else None,
        "employer_poc": cells[6].inner_text() if len(cells) > 6 else None,
        "poc_email": cells[7].inner_text() if len(cells) > 7 else None,
        "cost": cells[8].inner_text() if len(cells) > 8 else None,
        "closest_installation": cells[9].inner_text() if len(cells) > 9 else None,
        "opportunity_locations_by_state": cells[10].inner_text() if len(cells) > 10 else None,
        "delivery_method": cells[11].inner_text() if len(cells) > 11 else None,
        "target_mocs": cells[12].inner_text() if len(cells) > 12 else None,
        "other_eligibility_factors": cells[13].inner_text() if len(cells) > 13 else None,
        "other_prerequisite": cells[14].inner_text() if len(cells) > 14 else None,
        "jobs_description": cells[15].inner_text() if len(cells) > 15 else None,
        "summary_description": cells[16].inner_text() if len(cells) > 16 else None,
        "job_family": cells[17].inner_text() if len(cells) > 17 else None,
        "mou_organization": cells[18].inner_text() if len(cells) > 18 else None,
    }

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

def scrape_search_results(url: str, search_query: str) -> List[dict]:
    """Scrapes search results from a given URL and search query."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        page.fill(SEARCH_INPUT_SELECTOR, search_query)
        page.click(SEARCH_BUTTON_SELECTOR)
        page.wait_for_selector(TABLE_WRAPPER_SELECTOR)

        opportunities = []
        total_pages_element = page.query_selector(TOTAL_PAGES_SELECTOR)
        total_pages = int(total_pages_element.inner_text()) if total_pages_element else 1

        for _ in range(total_pages):
            rows = page.query_selector_all(ROW_SELECTOR)
            for row in rows:
                opportunity = extract_opportunity_data(row)
                if opportunity:
                    opportunities.append(opportunity.model_dump())

            next_page_button = page.query_selector(NEXT_PAGE_SELECTOR)
            if next_page_button:
                next_page_button.click()
                page.wait_for_timeout(PAGE_LOAD_DELAY) # Wait for a fixed amount of time
            else:
                break

        browser.close()
        return opportunities

def save_to_json(data: List[dict], filename: str) -> None:
    """Saves data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    target_url = "https://skillbridge.osd.mil/locations.htm"
    search_term = "*"

    results = scrape_search_results(target_url, search_term)

    print(f"Number of opportunities found: {len(results)}")

    filename = f"opportunities_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    save_to_json(results, filename)
    print(f"Data saved to {filename}")