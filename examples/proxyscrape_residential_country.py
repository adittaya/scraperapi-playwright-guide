"""ProxyScrape Residential with country targeting.

Append -country-XX to the username for country-specific IPs.
Example: username-country-in for India, username-country-us for USA.
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "YOUR_RESIDENTIAL_USERNAME"  # base username from dashboard
PASSWORD = "YOUR_RESIDENTIAL_PASSWORD"

# Append country to username
USERNAME_INDIA = f"{USERNAME}-country-in"

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
                "username": USERNAME_INDIA,
                "password": PASSWORD,
            }
        )
        page = await context.new_page()

        print("Checking IP through India residential proxy...")
        await page.goto("https://api.ipify.org?format=json", wait_until="commit", timeout=30000)
        print("IP:", await page.text_content("body"))

        await browser.close()

asyncio.run(main())
