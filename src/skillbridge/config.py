"""Configuration constants for the Skillbridge application."""

# Web scraping selectors
TABLE_WRAPPER_SELECTOR = "#location-table_wrapper"
ROW_SELECTOR = "#location-table > tbody > tr[role=\"row\"]"
SEARCH_INPUT_SELECTOR = "#keywords"
SEARCH_BUTTON_SELECTOR = "#loc-search-btn"
NEXT_PAGE_SELECTOR = "#location-table_next"
TOTAL_PAGES_SELECTOR = "#location-table_paginate > span > a:nth-child(5)"
PAGE_LOAD_DELAY = 500  # Milliseconds

# Database configuration
DEFAULT_DB_CONFIG = "dbname=postgres user=postgres host=localhost"

# Target URL
TARGET_URL = "https://skillbridge.osd.mil/locations.htm"
DEFAULT_SEARCH_TERM = "*"
