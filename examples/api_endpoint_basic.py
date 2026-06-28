"""
ScraperAPI API endpoint — basic usage.
Fetches pages via api.scraperapi.com instead of the proxy port.

Use case: When the proxy port blocks a domain ("protected domain" error),
the API endpoint with render=true can bypass this restriction.

How it differs from proxy port mode:
  - Returns rendered HTML (like a headless browser)
  - No interactive browser — use for content extraction, not clicks
  - Works for all domains including ScraperAPI-protected ones
  - Supports render=true for JavaScript execution

Usage:
    API_KEY=your_key python api_endpoint_basic.py

Requirements:
    pip install requests
"""

import requests

API_KEY = "YOUR_API_KEY"  # all lowercase


def fetch(url: str, render: bool = False, country: str = None) -> dict:
    """Fetch a page through ScraperAPI's API endpoint.

    Returns dict with: html, status, final_url, cookies, credits
    """
    params = [
        ("api_key", API_KEY),
        ("url", url),
    ]
    if render:
        params.append(("render", "true"))
    if country:
        params.append(("country_code", country))

    resp = requests.get(
        "http://api.scraperapi.com",
        params=params,
        timeout=60,
        headers={"User-Agent": "curl/8.0"},
    )
    resp.raise_for_status()

    return {
        "html": resp.text,
        "status": resp.status_code,
        "final_url": resp.headers.get("sa-final-url", url),
        "credits": resp.headers.get("sa-credit-cost", "?"),
        "cookies": dict(resp.cookies),
    }


def main():
    # Test 1: Basic fetch (no render, datacenter proxy, 1 credit)
    print("=== Test 1: Basic fetch ===")
    result = fetch("https://httpbin.org/ip")
    print(f"  HTTP {result['status']} | {len(result['html'])} bytes | "
          f"{result['credits']} credits")
    print(f"  Body: {result['html'][:80]}")

    # Test 2: With render=true (JS execution, ~10 credits)
    print("\n=== Test 2: With render=true ===")
    result = fetch("https://httpbin.org/ip", render=True)
    print(f"  HTTP {result['status']} | {len(result['html'])} bytes | "
          f"{result['credits']} credits")
    print(f"  IP: {result['html'][:80]}")

    # Test 3: With render=true + country targeting
    print("\n=== Test 3: India residential via API ===")
    result = fetch("https://api.ipify.org?format=json", render=True, country="in")
    print(f"  HTTP {result['status']} | {result['credits']} credits")
    print(f"  IP: {result['html'][:80]}")

    # Test 4: Protected domain — blocked on proxy port, works via API
    print("\n=== Test 4: Protected domain via API ===")
    result = fetch("https://example.com/protected-page", render=True)
    final = result["final_url"]
    print(f"  HTTP {result['status']} | {len(result['html'])} bytes | "
          f"{result['credits']} credits")
    print(f"  Final URL: {final}")
    print(f"  Cookies: {len(result['cookies'])}")


if __name__ == "__main__":
    main()
