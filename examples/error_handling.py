"""
ScraperAPI proxy with error handling and retry logic.
Handles common issues like rate limiting, timeouts, and auth errors.

Usage:
    API_KEY=your_key python error_handling.py
"""

import asyncio
import logging
import os
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraperapi")

API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")

PROXY = {"server": "http://proxy-server.scraperapi.com:8001"}

# Correct proxy credential format
CREDENTIALS = {
    "username": "scraperapi.premium=true",
    "password": API_KEY,
}

async def navigate_with_retry(
    url: str,
    max_retries: int = 3,
    base_delay: float = 5.0,
) -> str | None:
    """Navigate with exponential backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=PROXY,
                    args=["--no-sandbox", "--disable-gpu"],
                )
                context = await browser.new_context(
                    ignore_https_errors=True,  # REQUIRED
                    http_credentials=CREDENTIALS,
                )
                page = await context.new_page()
                await page.goto(url, wait_until="commit", timeout=60000)
                await browser.close()
                return page.url

        except Exception as e:
            delay = base_delay * attempt
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed: "
                f"{e.__class__.__name__}. Retrying in {delay}s..."
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)

    logger.error(f"All {max_retries} attempts failed for {url}")
    return None

async def main():
    # Test with a simple request first
    logger.info("Testing ScraperAPI proxy with retry logic...")

    url = await navigate_with_retry("https://httpbin.org/ip")
    if url:
        logger.info(f"Successfully reached: {url}")
    else:
        logger.error("Failed after all retries")

    # Check common errors
    print("\nCommon error checklist:")
    print("  [ ] API key is all lowercase")
    print("  [ ] ignore_https_errors=True is set")
    print("  [ ] Parameters use dots: scraperapi.param1=true.param2=value")
    print("  [ ] http_credentials used in new_context(), not in proxy")
    print("  [ ] API key is the password, scraperapi[.params] is the username")

asyncio.run(main())
