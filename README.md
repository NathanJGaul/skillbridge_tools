# Skillbridge Tools

A Python application for scraping and managing DoD SkillBridge opportunities.

## Project Structure

```
skillbridge_tools/
├── src/
│   └── skillbridge/
│       ├── __init__.py      # Package exports
│       ├── config.py        # Configuration constants
│       ├── schema.py        # Data models and validation
│       ├── scraper.py       # Web scraping functionality
│       └── database.py      # Database operations
├── main.py                  # Application entry point
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # Project documentation
```

## Modules

- **config.py**: Contains all configuration constants including selectors, delays, and default settings
- **schema.py**: Defines the data model for Skillbridge opportunities using Pydantic
- **scraper.py**: Implements web scraping logic using Playwright
- **database.py**: Handles data persistence (PostgreSQL and JSON)
- **main.py**: Entry point that coordinates the scraping and storage process

## Usage

Run the main script to scrape and store Skillbridge opportunities:

```bash
python main.py
```

This will:
1. Scrape opportunities from the DoD SkillBridge website
2. Save the results to a timestamped JSON file
3. Synchronize the data with a PostgreSQL database
