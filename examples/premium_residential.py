"""
ScraperAPI premium residential proxy example.
Uses residential IP pool with country targeting (India).

Usage:
    API_KEY=your_key python premium_residential.py

Key points:
    - premium=true activates residential/mobile IP pool
    - country_code=in targets Indian IPs
    - Parameters use DOT separator in username field
"""

import asyncio
import os
from playwright.async_api import async_playwright

API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")

PROFILES = {
    "datacenter": "scraperapi",
    "premium": "scraperapi.premium=true",
    "premium_india": "scraperapi.premium=true.country_code=in",
    "premium_us": "scraperapi.premium=true.country_code=us",
    "premium_render": "scraperapi.premium=true.render=true.country_code=us",
    "ultra_premium": "scraperapi.ultra_premium=true.country_code=us",
}

async def run_profile(profile_name: str, target_url: str) -> str | None:
    username = PROFILES[profile_name]
    print(f"\n[{profile_name}]")
    print(f"  Username: {username}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": "http://proxy-server.scraperapi.com:8001"},
            args=["--no-sandbox"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={"username": username, "password": API_KEY}
        )
        page = await context.new_page()

        try:
            await page.goto(target_url, wait_until="commit", timeout=30000)
            text = await page.text_content("body")
            print(f"  Response: {text.strip()[:100]}")
            return text
        except Exception as e:
            print(f"  Failed: {e}")
            return None
        finally:
            await browser.close()

async def main():
    # Test IP through different proxy profiles
    target = "https://api.ipify.org?format=json"

    for name in ["datacenter", "premium", "premium_india", "premium_us"]:
        await run_profile(name, target)

asyncio.run(main())
