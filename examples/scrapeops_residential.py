"""ScrapeOps Residential proxy example with Playwright.

Proxy gateway: residential-proxy.scrapeops.io:8181
Features: auto-rotating residential IPs on every request
Auth: username:password
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "scrapeops"
PASSWORD = "YOUR_API_KEY"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": "http://residential-proxy.scrapeops.io:8181"},
            args=["--no-sandbox"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={"username": USERNAME, "password": PASSWORD}
        )
        page = await context.new_page()

        print("Checking IP through ScrapeOps residential proxy...")
        await page.goto("https://api.ipify.org?format=json", wait_until="commit", timeout=30000)
        print("IP:", await page.text_content("body"))

        await browser.close()

asyncio.run(main())
