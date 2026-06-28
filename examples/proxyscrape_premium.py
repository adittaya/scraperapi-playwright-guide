"""ProxyScrape Premium Datacenter proxy example with Playwright.

Premium proxies use a proxy LIST (individual IP:port pairs), not a single gateway.
Get your proxy list from the dashboard and pick an IP:port to use.

Format: http://IP:PORT
Auth: customer-USER:PASS
"""
import asyncio
from playwright.async_api import async_playwright

# Get these from your ProxyScrape premium dashboard / API
PROXY_HOST = "151.123.177.10"  # pick an IP from your proxy list
PROXY_PORT = 3129               # HTTP port (3129), SOCKS5 port (1081)
USERNAME = "YOUR_PROXY_USERNAME"
PASSWORD = "YOUR_PROXY_PASSWORD"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": f"http://{PROXY_HOST}:{PROXY_PORT}"},
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

        print("Checking IP through Premium datacenter proxy...")
        await page.goto("https://api.ipify.org?format=json", wait_until="commit", timeout=30000)
        print("IP:", await page.text_content("body"))

        await browser.close()

asyncio.run(main())
