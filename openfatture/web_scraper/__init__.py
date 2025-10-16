"""OpenFatture Regulatory Web Scraper Module.

This module provides AI-powered web scraping capabilities for automatic regulatory updates.
It integrates with the existing RAG system to keep the knowledge base current with
the latest Italian tax regulations and FatturaPA specifications.

Key Features:
- Intelligent web scraping with anti-detection measures
- AI-powered content extraction and classification
- Regulatory change detection and validation
- Integration with ChromaDB vector store
- Compliance-focused design with audit trails

Architecture:
- RegulatoryWebScraper: Core scraping engine with Playwright
- ContentExtractor: AI-powered content parsing and structuring
- RegulatoryUpdateAgent: ReAct orchestration for update workflows
- RegulatoryUpdateService: Scheduling and orchestration service

Example Usage:
    >>> from openfatture.web_scraper import RegulatoryUpdateService
    >>> service = RegulatoryUpdateService()
    >>> await service.check_for_updates()
    >>> await service.update_knowledge_base()

Security & Compliance:
- Respects robots.txt and rate limits
- Only scrapes official government sources
- Maintains audit trails for all operations
- Human validation required for critical updates
"""

from .agent import RegulatoryUpdateAgent
from .config import WebScraperConfig, get_web_scraper_config
from .extractor import ContentExtractor
from .models import RegulatoryDocument, RegulatorySource, UpdateStatus
from .scraper import RegulatoryWebScraper
from .service import RegulatoryUpdateService

__all__ = [
    # Configuration
    "WebScraperConfig",
    "get_web_scraper_config",
    # Models
    "RegulatoryDocument",
    "RegulatorySource",
    "UpdateStatus",
    # Core Components
    "RegulatoryWebScraper",
    "ContentExtractor",
    "RegulatoryUpdateAgent",
    "RegulatoryUpdateService",
]
