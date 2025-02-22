import re
from datetime import datetime
import json
from dataclasses import dataclass
from playwright.sync_api import sync_playwright
from typing import Optional, List, Dict, Type, Any, ClassVar
from pydantic import BaseModel, Field, create_model
import psycopg2

TABLE_WRAPPER_SELECTOR = "#location-table_wrapper"
ROW_SELECTOR = "#location-table > tbody > tr[role=\"row\"]"
SEARCH_INPUT_SELECTOR = "#keywords"
SEARCH_BUTTON_SELECTOR = "#loc-search-btn"
NEXT_PAGE_SELECTOR = "#location-table_next"
TOTAL_PAGES_SELECTOR = "#location-table_paginate > span > a:nth-child(5)"
PAGE_LOAD_DELAY = 500  # Milliseconds

@dataclass
class SkillbridgeField:
    """Represents a field in the Skillbridge schema"""
    name: str
    type: Type
    description: str
    column_index: Optional[int] = None

class SkillbridgeSchema:
    """Central schema definition for Skillbridge opportunities"""
    fields: ClassVar[Dict[str, SkillbridgeField]] = {
        "id": SkillbridgeField("id", int, "Database ID"),
        "partner_program_agency": SkillbridgeField("partner_program_agency", str, "Partner/Program/Agency", 1),
        "service": SkillbridgeField("service", str, "Service", 2),
        "city": SkillbridgeField("city", str, "City", 3),
        "state": SkillbridgeField("state", str, "State", 4),
        "duration_of_training": SkillbridgeField("duration_of_training", str, "Duration of Training", 5),
        "employer_poc": SkillbridgeField("employer_poc", str, "Employer POC", 6),
        "poc_email": SkillbridgeField("poc_email", str, "POC Email", 7),
        "cost": SkillbridgeField("cost", str, "Cost", 8),
        "closest_installation": SkillbridgeField("closest_installation", str, "Closest Installation", 9),
        "opportunity_locations_by_state": SkillbridgeField("opportunity_locations_by_state", str, "Opportunity Locations by State", 10),
        "delivery_method": SkillbridgeField("delivery_method", str, "Delivery Method", 11),
        "target_mocs": SkillbridgeField("target_mocs", str, "Target MOCs", 12),
        "other_eligibility_factors": SkillbridgeField("other_eligibility_factors", str, "Other Eligibility Factors", 13),
        "other_prerequisite": SkillbridgeField("other_prerequisite", str, "Other/Prerequisite", 14),
        "jobs_description": SkillbridgeField("jobs_description", str, "Jobs Description", 15),
        "summary_description": SkillbridgeField("summary_description", str, "Summary Description", 16),
        "job_family": SkillbridgeField("job_family", str, "Job Family", 17),
        "mou_organization": SkillbridgeField("mou_organization", str, "MOU Organization", 18),
        "latitude": SkillbridgeField("latitude", float, "Latitude"),
        "longitude": SkillbridgeField("longitude", float, "Longitude"),
    }

    @classmethod
    def get_pydantic_model(cls) -> Type[BaseModel]:
        """Generates a Pydantic model from the schema"""
        field_definitions = {
            field.name: (Optional[field.type], Field(None, description=field.description))
            for field in cls.fields.values()
        }
        return create_model('SkillbridgeOpportunity', **field_definitions)

    @classmethod
    def get_db_columns(cls) -> List[str]:
        """Gets database column names from the schema"""
        return [field.name for field in cls.fields.values() if field.name != 'id']

    @classmethod
    def get_db_values(cls, data: Dict[str, Any]) -> tuple:
        """Gets database values in the correct order from data"""
        return tuple(data.get(field) for field in cls.get_db_columns())

    @classmethod
    def generate_identifier(cls, data: Dict[str, Any]) -> str:
        """Generates a unique identifier for an opportunity based on key fields"""
        key_fields = ['partner_program_agency', 'city', 'state']
        values = [str(data.get(field, '')).strip().lower() for field in key_fields]
        return '|'.join(values)

    @classmethod
    def has_changes(cls, new_data: Dict[str, Any], existing_data: Dict[str, Any]) -> bool:
        """Compares new data with existing data to detect changes"""
        fields_to_compare = [field for field in cls.get_db_columns() 
                           if field not in ['partner_program_agency', 'city', 'state']]
        
        for field in fields_to_compare:
            new_value = str(new_data.get(field, '')).strip()
            existing_value = str(existing_data.get(field, '')).strip()
            if new_value != existing_value:
                return True
        return False

# Create the Pydantic model from the schema
SkillbridgeOpportunity = SkillbridgeSchema.get_pydantic_model()

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

    data = {}
    
    # Extract data using schema field definitions
    for field in SkillbridgeSchema.fields.values():
        if field.column_index is not None and len(cells) > field.column_index:
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

def scrape_search_results(url: str, search_query: str) -> List[dict]:
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

def save_to_json(data: List[dict], filename: str) -> None:
    """Saves data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
        
def store_data_in_db(connection_string: str, data: List[dict]):
    """Stores or updates scraped data in the PostgreSQL database."""
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Get existing records
                columns = SkillbridgeSchema.get_db_columns()
                columns_str = ", ".join(columns)
                cur.execute(f"SELECT {columns_str} FROM skillbridge_opportunities")
                existing_records = {}
                for record in cur.fetchall():
                    record_dict = dict(zip(columns, record))
                    identifier = SkillbridgeSchema.generate_identifier(record_dict)
                    existing_records[identifier] = record_dict

                # Process each new record
                for item in data:
                    identifier = SkillbridgeSchema.generate_identifier(item)
                    values = SkillbridgeSchema.get_db_values(item)
                    
                    if identifier in existing_records:
                        if SkillbridgeSchema.has_changes(item, existing_records[identifier]):
                            # Update existing record
                            set_clause = ", ".join([f"{col} = %s" for col in columns])
                            update_query = f"""
                                UPDATE skillbridge_opportunities
                                SET {set_clause}
                                WHERE partner_program_agency = %s
                                AND city = %s
                                AND state = %s;
                            """
                            # Add identifier fields to values for WHERE clause
                            update_values = values + (
                                item.get('partner_program_agency'),
                                item.get('city'),
                                item.get('state')
                            )
                            cur.execute(update_query, update_values)
                    else:
                        # Insert new record
                        placeholders = ", ".join(["%s"] * len(columns))
                        insert_query = f"""
                            INSERT INTO skillbridge_opportunities (
                                {columns_str}
                            ) VALUES ({placeholders});
                        """
                        cur.execute(insert_query, values)

                conn.commit()
                print("Data successfully synchronized in the database.")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        raise

if __name__ == "__main__":
    target_url = "https://skillbridge.osd.mil/locations.htm"
    search_term = "*"
    connection_string = "dbname=postgres user=postgres host=localhost"

    results = scrape_search_results(target_url, search_term)

    print(f"Number of opportunities found: {len(results)}")

    filename = f"opportunities_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    save_to_json(results, filename)
    print(f"Data saved to {filename}")
    
    store_data_in_db(connection_string, results)
