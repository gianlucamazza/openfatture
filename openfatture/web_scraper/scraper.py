"""Regulatory web scraper with anti-detection measures."""

import asyncio
import hashlib
import json
import time
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from .config import WebScraperConfig
from .models import ContentType, RegulatoryDocument, RegulatorySource, UpdateStatus

logger = structlog.get_logger(__name__)


class RegulatoryWebScraper:
    """Intelligent web scraper for regulatory content with anti-detection measures.

    Features:
    - Playwright-based scraping with realistic browser behavior
    - Anti-detection measures (random delays, user agents, viewport rotation)
    - Rate limiting and robots.txt compliance
    - Content hashing for change detection
    - PDF and HTML content extraction
    - Error handling and retry logic
    """

    def __init__(self, config: WebScraperConfig):
        """Initialize the regulatory web scraper.

        Args:
            config: Web scraper configuration
        """
        self.config = config
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

        # Rate limiting
        self.last_request_time = 0.0
        self.domain_last_request: dict[str, float] = {}

        # Session tracking
        self.session_id = f"scrape_{int(time.time())}"

        logger.info(
            "regulatory_scraper_initialized",
            session_id=self.session_id,
            browser=self.config.browser_type,
            headless=self.config.headless,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> None:
        """Start the scraper with browser initialization."""
        if self.playwright:
            return

        self.playwright = await async_playwright().start()

        # Launch browser with anti-detection settings
        launch_options = {
            "headless": self.config.headless,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ],
        }

        if self.config.browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(**launch_options)
        elif self.config.browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(**launch_options)
        elif self.config.browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(**launch_options)

        # Create context with realistic settings
        self.context = await self.browser.new_context(
            user_agent=self.config.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="it-IT",
            timezone_id="Europe/Rome",
            permissions=["geolocation"],
            geolocation={"latitude": 41.9028, "longitude": 12.4964},  # Rome coordinates
        )

        # Add anti-detection scripts
        await self._setup_anti_detection()

        logger.info("scraper_started", browser=self.config.browser_type)

    async def stop(self) -> None:
        """Stop the scraper and cleanup resources."""
        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        logger.info("scraper_stopped")

    async def _setup_anti_detection(self) -> None:
        """Setup anti-detection measures."""
        if not self.context:
            return

        # Add scripts to make browser behavior more human-like
        await self.context.add_init_script(
            """
            // Override navigator properties
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            // Add realistic plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', description: '', filename: 'internal-nacl-plugin' }
                ]
            });

            // Add languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['it-IT', 'it', 'en-US', 'en']
            });
        """
        )

    async def scrape_source(self, source: RegulatorySource) -> list[RegulatoryDocument]:
        """Scrape a regulatory source and return documents.

        Args:
            source: Regulatory source configuration

        Returns:
            List of scraped regulatory documents
        """
        logger.info(
            "scraping_source_started",
            source_id=source.id,
            url=source.url,
            session_id=self.session_id,
        )

        documents = []

        try:
            # Check robots.txt compliance
            if self.config.respect_robots_txt:
                if not await self._check_robots_txt(source.url):
                    logger.warning("robots_txt_blocked", url=source.url)
                    return documents

            # Rate limiting
            await self._apply_rate_limiting(source.url)

            # Scrape main page
            main_doc = await self._scrape_page(source, source.url)
            if main_doc:
                documents.append(main_doc)

            # Follow links if configured
            if source.follow_links and source.link_selectors:
                link_docs = await self._scrape_links(source)
                documents.extend(link_docs)

        except Exception as e:
            logger.error(
                "scraping_source_failed", source_id=source.id, url=source.url, error=str(e)
            )

        logger.info(
            "scraping_source_completed", source_id=source.id, documents_scraped=len(documents)
        )

        return documents

    async def _scrape_page(self, source: RegulatorySource, url: str) -> RegulatoryDocument | None:
        """Scrape a single page.

        Args:
            source: Regulatory source configuration
            url: URL to scrape

        Returns:
            RegulatoryDocument if successful, None otherwise
        """
        if not self.context:
            raise RuntimeError("Scraper not started")

        try:
            page = await self.context.new_page()

            # Set random viewport for anti-detection
            await self._randomize_viewport(page)

            # Navigate with timeout and error handling
            response = await page.goto(url, timeout=30000, wait_until="networkidle")

            if not response or not response.ok:
                logger.warning(
                    "page_load_failed", url=url, status=response.status if response else None
                )
                await page.close()
                return None

            # Wait for content to load
            await page.wait_for_timeout(2000)

            # Extract content based on type
            if source.content_type == ContentType.HTML:
                content, title = await self._extract_html_content(page, source)
            elif source.content_type == ContentType.PDF:
                content, title = await self._extract_pdf_content(page, url)
            else:
                content, title = await self._extract_text_content(page)

            await page.close()

            if not content:
                return None

            # Create document
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            document = RegulatoryDocument(
                source_id=source.id,
                source_name=source.name,
                url=url,
                title=title or f"Document from {source.name}",
                content=content,
                content_hash=content_hash,
                content_type=source.content_type.value,
                jurisdiction=source.jurisdiction,
                category=source.category,
                tags=source.tags,
                status=UpdateStatus.PENDING,
                requires_review=self.config.require_human_review,
            )

            # Save raw content if configured
            if self.config.cache_dir:
                await self._save_raw_content(document)

            return document

        except Exception as e:
            logger.error("page_scraping_failed", url=url, error=str(e))
            return None

    async def _extract_html_content(self, page: Page, source: RegulatorySource) -> tuple[str, str]:
        """Extract content from HTML page using selectors.

        Args:
            page: Playwright page
            source: Source configuration with selectors

        Returns:
            Tuple of (content, title)
        """
        # Extract title
        title = await page.title() or "Untitled Document"

        # Extract main content using selectors
        content_parts = []

        if source.selectors:
            for selector_name, selector in source.selectors.items():
                try:
                    elements = page.locator(selector)
                    count = await elements.count()

                    for i in range(count):
                        element = elements.nth(i)
                        text = await element.text_content()
                        if text and text.strip():
                            content_parts.append(f"## {selector_name}\n{text.strip()}")
                except Exception as e:
                    logger.warning("selector_extraction_failed", selector=selector, error=str(e))
        else:
            # Fallback: extract all text
            content = await page.locator("body").text_content()
            content_parts.append(content or "")

        content = "\n\n".join(content_parts)

        # Clean up content
        content = self._clean_content(content)

        return content, title

    async def _extract_pdf_content(self, page: Page, url: str) -> tuple[str, str]:
        """Extract content from PDF (download and parse).

        Args:
            page: Playwright page
            url: PDF URL

        Returns:
            Tuple of (content, title)
        """
        import io

        from pypdf import PdfReader

        try:
            # Download PDF content using httpx
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True, headers={"User-Agent": self.config.user_agent}
            ) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    logger.warning("pdf_download_failed", url=url, status=response.status_code)
                    return "", f"PDF Document from {urlparse(url).netloc}"

                pdf_bytes = response.content

            # Extract text from PDF
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)

            # Extract text from all pages
            content_parts = []
            for page_num in range(len(pdf_reader.pages)):
                pdf_page = pdf_reader.pages[page_num]
                text = pdf_page.extract_text()
                if text.strip():
                    content_parts.append(text.strip())

            content = "\n\n".join(content_parts)

            # Try to get title from PDF metadata
            metadata = pdf_reader.metadata
            title = metadata.get("/Title", "").strip() if metadata else ""
            if not title:
                title = f"PDF Document from {urlparse(url).netloc}"

            # Clean content
            content = self._clean_content(content)

            logger.info(
                "pdf_content_extracted",
                url=url,
                pages=len(pdf_reader.pages),
                content_length=len(content),
            )

            return content, title

        except Exception as e:
            logger.error("pdf_extraction_failed", url=url, error=str(e))
            # Fallback: return basic info
            title = f"PDF Document from {urlparse(url).netloc}"
            content = f"PDF content extraction failed: {str(e)}"
            return content, title

    async def _extract_text_content(self, page: Page) -> tuple[str, str]:
        """Extract plain text content.

        Args:
            page: Playwright page

        Returns:
            Tuple of (content, title)
        """
        title = await page.title() or "Text Document"
        content = await page.locator("body").text_content() or ""
        content = self._clean_content(content)

        return content, title

    async def _scrape_links(self, source: RegulatorySource) -> list[RegulatoryDocument]:
        """Scrape linked pages from a source.

        Args:
            source: Source configuration

        Returns:
            List of documents from linked pages
        """
        if not self.context:
            return []

        documents = []

        try:
            page = await self.context.new_page()
            await page.goto(source.url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(1000)

            # Extract links
            links = []
            for selector in source.link_selectors:
                try:
                    link_elements = page.locator(selector)
                    count = await link_elements.count()

                    for i in range(min(count, 10)):  # Limit to 10 links per selector
                        href = await link_elements.nth(i).get_attribute("href")
                        if href:
                            full_url = urljoin(source.url, href)
                            if self._is_allowed_url(full_url):
                                links.append(full_url)
                except Exception as e:
                    logger.warning("link_extraction_failed", selector=selector, error=str(e))

            await page.close()

            # Remove duplicates and scrape each link
            unique_links = list(set(links))
            for link_url in unique_links[:5]:  # Limit to 5 links
                await self._apply_rate_limiting(link_url)
                doc = await self._scrape_page(source, link_url)
                if doc:
                    documents.append(doc)

        except Exception as e:
            logger.error("link_scraping_failed", source_id=source.id, error=str(e))

        return documents

    async def _check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False if blocked
        """
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            async with httpx.AsyncClient() as client:
                response = await client.get(robots_url, timeout=10)
                if response.status_code == 200:
                    # Simple robots.txt parsing (could be more sophisticated)
                    robots_content = response.text
                    user_agent_line = f"User-agent: {self.config.user_agent.split()[0]}"
                    disallow_lines = []

                    in_relevant_section = False
                    for line in robots_content.split("\n"):
                        line = line.strip().lower()
                        if line.startswith("user-agent:"):
                            in_relevant_section = (
                                "*" in line or self.config.user_agent.lower() in line
                            )
                        elif in_relevant_section and line.startswith("disallow:"):
                            disallow_lines.append(line.replace("disallow:", "").strip())

                    # Check if our path is disallowed
                    path = parsed.path or "/"
                    for disallow in disallow_lines:
                        if disallow == "/" or path.startswith(disallow.rstrip("*")):
                            return False

            return True

        except Exception as e:
            logger.warning("robots_txt_check_failed", url=url, error=str(e))
            return True  # Allow if we can't check

    async def _apply_rate_limiting(self, url: str) -> None:
        """Apply rate limiting for requests.

        Args:
            url: URL being requested
        """
        domain = urlparse(url).netloc

        # Global rate limiting
        now = time.time()
        time_since_last = now - self.last_request_time
        min_interval = 60.0 / self.config.requests_per_minute

        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)

        # Domain-specific rate limiting
        domain_last = self.domain_last_request.get(domain, 0)
        time_since_domain = now - domain_last

        if time_since_domain < self.config.delay_between_requests:
            await asyncio.sleep(self.config.delay_between_requests - time_since_domain)

        # Add random delay for anti-detection
        await asyncio.sleep(
            self.config.delay_between_requests * 0.1 * (0.5 + 0.5 * time.time() % 1)
        )

        self.last_request_time = time.time()
        self.domain_last_request[domain] = time.time()

    async def _randomize_viewport(self, page: Page) -> None:
        """Randomize viewport size for anti-detection.

        Args:
            page: Playwright page
        """
        import random

        widths = [1920, 1366, 1536, 1440, 1280]
        heights = [1080, 768, 864, 900, 1024]

        width = random.choice(widths)
        height = random.choice(heights)

        await page.set_viewport_size({"width": width, "height": height})

    def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is allowed based on configuration.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        if self.config.require_https and not url.startswith("https://"):
            return False

        domain = urlparse(url).netloc
        return domain in self.config.allowed_domains

    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content.

        Args:
            content: Raw content

        Returns:
            Cleaned content
        """
        if not content:
            return ""

        # Remove excessive whitespace
        import re

        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r" {2,}", " ", content)

        # Remove common noise
        content = re.sub(r"\b\d{1,2}/\d{1,2}/\d{4}\b", "", content)  # Dates
        content = re.sub(r"\b\d+\.\d+\.\d+\.\d+\b", "", content)  # IPs

        return content.strip()

    async def _save_raw_content(self, document: RegulatoryDocument) -> None:
        """Save raw content to cache directory.

        Args:
            document: Document to save
        """
        try:
            cache_path = self.config.cache_dir / f"{document.content_hash}.json"

            data = {
                "source_id": document.source_id,
                "url": document.url,
                "title": document.title,
                "content": document.content,
                "content_hash": document.content_hash,
                "scraped_at": document.scraped_at.isoformat(),
                "metadata": {
                    "content_type": document.content_type,
                    "jurisdiction": document.jurisdiction,
                    "category": document.category,
                    "tags": document.tags,
                },
            }

            cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

            # Update document path
            document.raw_content_path = str(cache_path)

        except Exception as e:
            logger.warning("raw_content_save_failed", error=str(e))
