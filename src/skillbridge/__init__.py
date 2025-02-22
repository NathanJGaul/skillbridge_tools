"""Skillbridge package for scraping and managing DoD SkillBridge opportunities."""

from .config import (
    TARGET_URL,
    DEFAULT_SEARCH_TERM,
    DEFAULT_DB_CONFIG
)
from .schema import SkillbridgeOpportunity, SkillbridgeSchema
from .scraper import scrape_search_results
from .database import save_to_json, store_data_in_db

__all__ = [
    'TARGET_URL',
    'DEFAULT_SEARCH_TERM',
    'DEFAULT_DB_CONFIG',
    'SkillbridgeOpportunity',
    'SkillbridgeSchema',
    'scrape_search_results',
    'save_to_json',
    'store_data_in_db',
]
