"""ProxyScrape Residential proxy example with Playwright.

Proxy gateway: rp.scrapegw.com:6060
Auth: username:password from dashboard
Country targeting: append -country-XX to username
Sticky sessions: append -session-{id}-lifetime-{minutes} to username
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "YOUR_RESIDENTIAL_USERNAME"
PASSWORD = "YOUR_RESIDENTIAL_PASSWORD"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": "http://rp.scrapegw.com:6060"},
            args=["--no-sandbox"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={
                "username": USERNAME,
                "password": PASSWORD,
            }
        )
        page = await context.new_page()

        print("Checking IP through ProxyScrape residential proxy...")
        await page.goto("https://api.ipify.org?format=json", wait_until="commit", timeout=30000)
        print("IP:", await page.text_content("body"))

        print("Navigating to target site...")
        await page.goto("https://example.com", wait_until="commit", timeout=60000)
        print("Final URL:", page.url)

        await browser.close()

asyncio.run(main())
