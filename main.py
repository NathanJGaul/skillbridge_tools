"""Main entry point for the Skillbridge scraper application."""

from src.skillbridge import (
    TARGET_URL,
    DEFAULT_SEARCH_TERM,
    DEFAULT_DB_CONFIG,
    scrape_search_results,
    save_to_json,
    store_data_in_db,
)

def main():
    """Main function to run the Skillbridge scraper."""
    # Scrape opportunities data
    results = scrape_search_results(TARGET_URL, DEFAULT_SEARCH_TERM)
    print(f"Number of opportunities found: {len(results)}")

    # Save to JSON and database
    save_to_json(results)
    store_data_in_db(DEFAULT_DB_CONFIG, results)

if __name__ == "__main__":
    main()
