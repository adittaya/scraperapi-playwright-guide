"""
Basic ScraperAPI proxy test with Playwright.
Tests basic connectivity through the proxy port.

Usage:
    API_KEY=your_key python basic_usage.py

Requirements:
    pip install playwright
    playwright install chromium
"""

import asyncio
import os
from playwright.async_api import async_playwright

API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": "http://proxy-server.scraperapi.com:8001"},
            args=["--no-sandbox"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={"username": "scraperapi", "password": API_KEY}
        )
        page = await context.new_page()

        try:
            await page.goto(
                "https://httpbin.org/ip",
                wait_until="commit",
                timeout=30000
            )
            print("Response:", await page.text_content("body"))
        except Exception as e:
            print(f"Failed: {e}")
        finally:
            await browser.close()

asyncio.run(main())
