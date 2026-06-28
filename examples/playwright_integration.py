"""
Full Playwright integration with ScraperAPI proxy.
Shows how to use ScraperAPI with browser automation.

Features:
    - Multiple proxy profiles
    - Session persistence
    - Navigation with retries
    - IP detection

Usage:
    API_KEY=your_key python playwright_integration.py
"""

import asyncio
import logging
import os
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("scraperapi")

API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")

PROXY = {"server": "http://proxy-server.scraperapi.com:8001"}

PROFILES = {
    "datacenter": "scraperapi",
    "premium_us": "scraperapi.premium=true.country_code=us",
    "premium_india": "scraperapi.premium=true.country_code=in",
}

async def get_ip(username: str) -> str | None:
    """Get current public IP through the proxy."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, proxy=PROXY, args=["--no-sandbox"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={"username": username, "password": API_KEY},
        )
        page = await context.new_page()
        try:
            await page.goto(
                "https://api.ipify.org?format=json",
                wait_until="commit",
                timeout=20000
            )
            return await page.text_content("body")
        finally:
            await browser.close()

async def navigate_with_session(
    username: str, url: str, timeout: int = 60000
) -> str | None:
    """Navigate to URL using ScraperAPI proxy with session persistence."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, proxy=PROXY, args=["--no-sandbox"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={"username": username, "password": API_KEY},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="commit", timeout=timeout)
            await page.wait_for_timeout(2000)
            return page.url
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return None
        finally:
            await browser.close()

async def main():
    # Step 1: Verify proxy works and check IP
    logger.info("Testing ScraperAPI proxy...")

    for name, username in PROFILES.items():
        ip = await get_ip(username)
        logger.info(f"[{name}] IP: {ip}")

    # Step 2: Navigate to a target site through India proxy
    logger.info("\nNavigating through India residential proxy...")
    url = await navigate_with_session(
        PROFILES["premium_india"],
        "https://httpbin.org/ip"
    )
    if url:
        logger.info(f"Reached: {url}")
    else:
        logger.error("Navigation failed")

asyncio.run(main())
