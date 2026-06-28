"""ScrapeOps IP rotation test — shows a new residential IP on every request."""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "scrapeops"
PASSWORD = "YOUR_API_KEY"

async def get_ip():
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
        await page.goto("https://api.ipify.org?format=json", wait_until="commit", timeout=30000)
        ip = await page.text_content("body")
        await browser.close()
        return ip

async def main():
    for i in range(5):
        ip = await get_ip()
        print(f"Request {i+1}: {ip}")

asyncio.run(main())
