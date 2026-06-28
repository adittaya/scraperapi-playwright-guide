"""
ScraperAPI API endpoint + Playwright — hybrid approach for protected domains.

Problem:
  The proxy port (proxy-server.scraperapi.com:8001) blocks certain
  domains with "Protected domains may require premium=true" even when
  premium=true is set. This is an account-level restriction.

Solution:
  Use the API endpoint (api.scraperapi.com?render=true) to fetch the
  initial page. It bypasses the domain restriction and returns the
  fully rendered HTML after JavaScript execution.

  Then inject the cookies + redirect URL into Playwright for
  interactive automation (clicks, navigation, forms, etc.).

Flow:
  1. Fetch target URL via ScraperAPI API endpoint (render=true)
  2. Extract final URL + cookies from API response
  3. Launch Playwright (no proxy needed for subsequent hops)
  4. Inject cookies into browser context
  5. Navigate to the redirect URL
  6. Continue with normal Playwright automation

Usage:
    API_KEY=your_key python api_endpoint_protected_domains.py

Requirements:
    pip install requests playwright
    playwright install chromium
"""

import asyncio
import os

import requests
from playwright.async_api import async_playwright

API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")

# ── API Endpoint ─────────────────────────────────────────────────────────────

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def api_fetch(url: str, render: bool = True, country: str = None) -> dict:
    """Fetch a page through ScraperAPI's API endpoint."""
    params = [("api_key", API_KEY), ("url", url)]
    if render:
        params.append(("render", "true"))
    if country:
        params.append(("country_code", country))

    resp = requests.get(
        "http://api.scraperapi.com",
        params=params,
        timeout=90,
        headers={"User-Agent": "curl/8.0"},
    )
    resp.raise_for_status()

    cookies = [
        {"name": c.name, "value": c.value,
                 "domain": c.domain.lstrip(".") if c.domain else "example.com",
         "path": c.path or "/"}
        for c in resp.cookies
    ]

    return {
        "html": resp.text,
        "status": resp.status_code,
        "final_url": resp.headers.get("sa-final-url", url),
        "credits": resp.headers.get("sa-credit-cost", "?"),
        "cookies": cookies,
    }


# ── Playwright Integration ───────────────────────────────────────────────────

async def navigate_with_api_proxy(
    target_url: str,
    country: str = None,
    headless: bool = True,
) -> str | None:
    """
    Navigate to target_url through ScraperAPI API endpoint,
    then continue with Playwright for interactive automation.
    """
    # Step 1: Fetch via API endpoint
    print(f"[1/4] Fetching via ScraperAPI API: {target_url}")
    result = api_fetch(target_url, render=True, country=country)
    start_url = result["final_url"]
    print(f"       HTTP {result['status']}, {len(result['html'])} bytes, "
          f"{result['credits']} credits")
    print(f"       Redirect target: {start_url}")
    print(f"       Cookies: {len(result['cookies'])}")

    # Step 2: Launch Playwright
    print(f"[2/4] Launching Playwright...")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-gpu"],
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720},
        )

        # Step 3: Inject cookies from API response
        if result["cookies"]:
            print(f"[3/4] Injecting {len(result['cookies'])} cookies...")
            try:
                await context.add_cookies(result["cookies"])
            except Exception as e:
                print(f"       Cookie warning: {e}")

        # Step 4: Navigate and interact
        page = await context.new_page()
        print(f"[4/4] Navigating to: {start_url}")
        await page.goto(start_url, wait_until="commit", timeout=60000)
        print(f"       Page URL: {page.url}")
        print(f"       Page title: {await page.title()}")

        # Now you can interact with the page normally
        # (click buttons, fill forms, extract data, etc.)
        body = await page.text_content("body") or ""
        print(f"       Body: {len(body)} chars")

        await browser.close()
        return page.url


async def main():
    # Test: Protected domain that fails on proxy port
    target = "https://example.com/protected-page"
    print(f"\n{'=' * 60}")
    print(f"  Target: {target}")
    print(f"{'=' * 60}\n")

    url = await navigate_with_api_proxy(
        target_url=target,
        country="in",
        headless=True,
    )
    print(f"\n  Final URL: {url}")


if __name__ == "__main__":
    asyncio.run(main())
