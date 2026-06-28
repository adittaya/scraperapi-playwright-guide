# ScraperAPI + Playwright: Complete Proxy Configuration Guide

A comprehensive guide to configuring **ScraperAPI residential/mobile proxy pools** with **Playwright (Python)** for browser automation.

## Why This Guide?

ScraperAPI's documentation covers the API endpoint and basic proxy usage, but configuring the **proxy port mode** with **Playwright's browser automation** has specific requirements that aren't obvious. This guide fills that gap with **working, tested configurations**.

## What You'll Learn

- Correct proxy authentication format for Playwright
- Residential (`premium=true`) vs mobile proxy configuration
- Country-specific IP targeting (India, US, etc.)
- Common pitfalls and how to avoid them
- Full working examples

---

## Table of Contents

- [Quick Start](#quick-start)
- [How ScraperAPI Proxy Works](#how-scraperapi-proxy-works)
- [Playwright Configuration](#playwright-configuration)
- [Residential & Mobile Proxies](#residential--mobile-proxies)
- [Country Targeting](#country-targeting)
- [Complete Examples](#complete-examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Quick Start

```python
import asyncio
from playwright.async_api import async_playwright

API_KEY = "YOUR_API_KEY"  # all lowercase

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": "http://proxy-server.scraperapi.com:8001"},
            args=["--no-sandbox", "--disable-gpu"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,  # REQUIRED for ScraperAPI
            http_credentials={
                "username": "scraperapi",
                "password": API_KEY,
            }
        )
        page = await context.new_page()
        await page.goto("https://httpbin.org/ip", wait_until="commit", timeout=30000)
        print(await page.text_content("body"))
        await browser.close()

asyncio.run(main())
```

---

## How ScraperAPI Proxy Works

ScraperAPI provides a **proxy port** (`proxy-server.scraperapi.com:8001`) that acts as a forward HTTP proxy. All requests go through this proxy, which handles:

- IP rotation
- CAPTCHA solving
- Anti-bot detection bypass
- JavaScript rendering (with `render=true`)
- Residential/mobile proxy pools (with `premium=true`)

### Proxy Port vs API Endpoint

| Feature | Proxy Port (`:8001`) | API Endpoint |
|---------|---------------------|--------------|
| Browser automation | ✅ Full browser support | ❌ HTML only |
| JavaScript rendering | ✅ Via `render=true` | ✅ Via `render=true` |
| Real-time interaction | ✅ Click, scroll, wait | ❌ Static response |
| Session persistence | ✅ Cookies, localStorage | ❌ Per-request |
| Authentication | HTTP Basic Auth | Query parameter |

For **Playwright/Puppeteer/Selenium** automation, the **proxy port mode** is the correct choice.

---

## API Endpoint Mode (For Protected Domains)

The proxy port blocks certain domains with "Protected domains may require premium=true" — even with `premium=true` set, some domains are blocked at the account level. The **API endpoint** (`api.scraperapi.com`) bypasses this restriction.

### When to Use API Endpoint

| Situation | Proxy Port | API Endpoint |
|-----------|-----------|--------------|
| Normal websites | ✅ Works | ✅ Works (more expensive) |
| Protected domains | ❌ Blocked | ✅ Works |
| Need click/scroll | ✅ Playwright | ❌ Static HTML only |
| Session persistence | ✅ Cookies preserved | ❌ Per-request |
| Cost | 1 credit/req (datacenter) | 1 credit (no render) / ~10 credits (render) |

### Basic API Endpoint Usage

The API endpoint is simple HTTP — no Playwright required for content extraction:

```python
import requests

API_KEY = "YOUR_API_KEY"

# Without render (datacenter proxy, 1 credit)
resp = requests.get("http://api.scraperapi.com", params={
    "api_key": API_KEY,
    "url": "https://httpbin.org/ip",
})
print(resp.text)  # {"ip": "..."}

# With render (headless browser, ~10 credits)
resp = requests.get("http://api.scraperapi.com", params={
    "api_key": API_KEY,
    "url": "https://example.com/js-heavy-page",
    "render": "true",
})
```

### Hybrid: API Endpoint + Playwright for Interactive Pages

When you need both protected-domain access *and* interactive automation:

1. **Fetch** the page via API endpoint (`render=true`) to get the redirect URL + cookies
2. **Inject** cookies into a Playwright context (no proxy)
3. **Navigate** to the redirect URL and interact normally

```python
import asyncio
import requests
from playwright.async_api import async_playwright

API_KEY = "YOUR_API_KEY"

async def hybrid_approach(target_url: str):
    # Step 1: Fetch via API endpoint (bypasses domain block)
    resp = requests.get("http://api.scraperapi.com", params={
        "api_key": API_KEY,
        "url": target_url,
        "render": "true",
    }, timeout=90)
    redirect_url = resp.headers.get("sa-final-url", target_url)
    cookies = [
        {"name": c.name, "value": c.value,
         "domain": c.domain.lstrip(".") if c.domain else "example.com",
         "path": c.path or "/"}
        for c in resp.cookies
    ]

    # Step 2: Launch Playwright and inject cookies
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        if cookies:
            await context.add_cookies(cookies)

        # Step 3: Navigate to the redirect URL (no proxy needed)
        page = await context.new_page()
        await page.goto(redirect_url, wait_until="commit", timeout=60000)
        print(f"Page URL: {page.url}")

        # Now you can click, scroll, fill forms, etc.
        # page.click("button#continue")
        # page.wait_for_selector("div.result")

        await browser.close()

asyncio.run(hybrid_approach("https://example.com/protected-page"))
```

### Key Differences from Proxy Port

- **No `http_credentials`** — authentication is via `api_key` query parameter
- **No `ignore_https_errors=True`** — API endpoint returns HTTPS content directly
- **No interactive browser** — API endpoint returns raw HTML (use `render=true` for JS rendering)
- **Session via cookies** — extract `Set-Cookie` headers and inject into Playwright
- **Redirect tracking** — `sa-final-url` response header reveals the final destination after all redirects

### Cost Comparison

| Mode | Credits |
|------|---------|
| Port mode (datacenter) | 1 |
| Port mode (premium) | 10 |
| Port mode (premium + render) | 25 |
| API endpoint (no render) | 1 |
| API endpoint (render) | ~10 |
| Ultra premium | 30 |

---



## Playwright Configuration

### The Right Way: `http_credentials` in Context

```python
# CORRECT - works with all ScraperAPI features
browser = await p.chromium.launch(
    proxy={"server": "http://proxy-server.scraperapi.com:8001"}
)
context = await browser.new_context(
    ignore_https_errors=True,
    http_credentials={
        "username": "scraperapi.premium=true.country_code=in",
        "password": API_KEY,
    }
)
```

### The Wrong Way (Don't Do This)

```python
# WRONG - API key in username field
proxy = {
    "server": "http://proxy-server.scraperapi.com:8001",
    "username": f"{API_KEY}&render=true&residential=true",  # BAD
    "password": "",  # BAD
}

# ALSO WRONG - params with wrong separator
proxy = {
    "server": "http://proxy-server.scraperapi.com:8001",
    "username": "scraperapi.render=true&premium=true",  # Use '.' not '&'
    "password": API_KEY,
}
```

### Why? 

Playwright's `proxy` parameter sends credentials via HTTP Basic Auth for the CONNECT tunnel but the ScraperAPI proxy reads parameters from the **username field** using dot-separated format. The `http_credentials` in `new_context()` ensures proper credential passing.

---

## Residential & Mobile Proxies

### Parameter Reference

| Parameter | Effect | Credit Cost |
|-----------|--------|-------------|
| (none) | Datacenter proxy pool | 1 credit/request |
| `premium=true` | Residential + mobile IPs | 10 credits/request |
| `premium=true` + `render=true` | Residential + JS rendering | 25 credits/request |
| `ultra_premium=true` | High-tier residential pool | 30 credits/request |

### Residential Proxy (Premium)

```python
http_credentials = {
    "username": "scraperapi.premium=true",
    "password": API_KEY,
}
```

### Residential with Country Targeting

```python
http_credentials = {
    "username": "scraperapi.premium=true.country_code=in",
    "password": API_KEY,
}
```

### With JavaScript Rendering

```python
http_credentials = {
    "username": "scraperapi.premium=true.render=true.country_code=in",
    "password": API_KEY,
}
```

### Ultra Premium

```python
http_credentials = {
    "username": "scraperapi.ultra_premium=true.country_code=in",
    "password": API_KEY,
}
```

---

## Country Targeting

Supported countries for residential proxies:

| Country | Code | IPs Available |
|---------|------|---------------|
| United States | `country_code=us` | 5,121,722 |
| India | `country_code=in` | 3,574,624 |
| United Kingdom | `country_code=uk` | 298,962 |
| Canada | `country_code=ca` | 119,346 |
| Germany | `country_code=de` | 321,736 |
| France | `country_code=fr` | 272,436 |
| Spain | `country_code=es` | 92,278 |
| Mexico | `country_code=mx` | 78,327 |
| Japan | `country_code=jp` | 286,142 |
| China | `country_code=cn` | 358,963 |
| Australia | `country_code=au` | 142,857 |
| Brazil | `country_code=br` | 62,552 |

**Available on Business/Enterprise plans only** for most non-US/EU countries.

---

## Complete Examples

### Basic Proxy Test

```python
# examples/basic_usage.py
import asyncio
from playwright.async_api import async_playwright

API_KEY = "YOUR_API_KEY"

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

        await page.goto("https://httpbin.org/ip", wait_until="commit", timeout=30000)
        print("Response:", await page.text_content("body"))

        await browser.close()

asyncio.run(main())
```

### Premium Residential India Proxy

```python
# examples/premium_residential.py
import asyncio
from playwright.async_api import async_playwright

API_KEY = "YOUR_API_KEY"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": "http://proxy-server.scraperapi.com:8001"},
            args=["--no-sandbox"]
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={
                "username": "scraperapi.premium=true.country_code=in",
                "password": API_KEY,
            }
        )
        page = await context.new_page()

        print("Checking IP through India residential proxy...")
        await page.goto("https://api.ipify.org?format=json", wait_until="commit", timeout=30000)
        print("IP:", await page.text_content("body"))

        print("Navigating to target site...")
        await page.goto("https://example.com", wait_until="commit", timeout=60000)
        print("Final URL:", page.url)

        await browser.close()

asyncio.run(main())
```

### Full Playwright Integration

```python
# examples/playwright_integration.py
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraperapi")

API_KEY = "YOUR_API_KEY"

PROXY_CONFIG = {
    "server": "http://proxy-server.scraperapi.com:8001",
}

# Choose your proxy profile:
PROFILES = {
    "datacenter": "scraperapi",
    "premium_us": "scraperapi.premium=true.country_code=us",
    "premium_india": "scraperapi.premium=true.country_code=in",
    "premium_render": "scraperapi.premium=true.render=true.country_code=us",
    "ultra_premium": "scraperapi.ultra_premium=true.country_code=us",
}

async def run_with_profile(profile: str, target_url: str):
    username = PROFILES.get(profile, PROFILES["datacenter"])
    logger.info(f"Using profile: {profile} -> {username}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=PROXY_CONFIG,
            args=["--no-sandbox", "--disable-gpu"],
        )
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={"username": username, "password": API_KEY},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(target_url, wait_until="commit", timeout=60000)
            logger.info(f"Success! URL: {page.url}")
            return page.url
        except Exception as e:
            logger.error(f"Failed: {e}")
            return None
        finally:
            await browser.close()

async def main():
    # Test with premium India proxy
    result = await run_with_profile("premium_india", "https://httpbin.org/ip")
    print("Result:", result)

asyncio.run(main())
```

### Error Handling

```python
# examples/error_handling.py
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraperapi")

API_KEY = "YOUR_API_KEY"

async def safe_navigate_with_retry(url: str, max_retries: int = 3):
    for attempt in range(1, max_retries + 1):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    proxy={"server": "http://proxy-server.scraperapi.com:8001"},
                    args=["--no-sandbox"]
                )
                context = await browser.new_context(
                    ignore_https_errors=True,
                    http_credentials={
                        "username": "scraperapi.premium=true",
                        "password": API_KEY,
                    }
                )
                page = await context.new_page()
                await page.goto(url, wait_until="commit", timeout=60000)
                await browser.close()
                return page.url
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(5)
    return None

async def main():
    url = await safe_navigate_with_retry("https://httpbin.org/ip")
    if url:
        logger.info(f"Reached: {url}")
    else:
        logger.error("All attempts failed")

asyncio.run(main())
```

---

## Troubleshooting

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Wrong API key format | Use **all lowercase** API key |
| `500 Internal Server Error` | API endpoint with `urllib` | Use `requests` library instead of `urllib` |
| `Protected domain` | Account-level domain block | Use API endpoint mode (`api.scraperapi.com?render=true`) instead of proxy port |
| `"plan not allowed"` | Ultra premium not on plan | Fall back to `premium=true` or API endpoint |
| `ERR_TUNNEL_CONNECTION_FAILED` | Proxy auth failure | Use `http_credentials` in context, not proxy URL |
| `ERR_EMPTY_RESPONSE` | Rate limited or blocked domain | Wait 30s and retry; check credit balance |
| `ERR_PROXY_CONNECTION_FAILED` | Wrong auth format | Username must start with `scraperapi[.params]` |
| `net::ERR_CERT_AUTHORITY_INVALID` | SSL cert issue | Set `ignore_https_errors=True` |

### Debug Checklist

1. ✅ API key is **all lowercase** (e.g., `ef3c62...` not `Ef3c62...`)
2. ✅ `ignore_https_errors=True` is set in `new_context()`
3. ✅ Parameters use **dot** separator: `scraperapi.premium=true.country_code=in`
4. ✅ `http_credentials` used in `new_context()`, not in `launch(proxy=...)`
5. ✅ API key is the **password**, `scraperapi[.params]` is the **username**
6. ✅ No `render=true` and `residential=true` together (these are for API endpoint, not proxy port)
7. ✅ Test first with `https://httpbin.org/ip` before your target URL

### Rate Limiting

ScraperAPI's free plan (1000 requests/month) can get rate-limited quickly during testing. If you see empty responses:

```python
# Wait 30 seconds between test runs to avoid rate limiting
await asyncio.sleep(30)
```

---

## Best Practices

1. **Store API key in environment variables**, never hardcode
2. **Use `wait_until="commit"`** for faster page loads (instead of `"networkidle"`)
3. **Set `ignore_https_errors=True`** — required for ScraperAPI's custom CA
4. **Start with `https://httpbin.org/ip`** to verify proxy works before hitting your target
5. **Use `country_code` for geo-targeting** — residential proxies geo-located to the specified country
6. **Reuse browser contexts** for session persistence across pages
7. **Implement retry logic** with backoff for transient failures

---

# ProxyScrape + Playwright Configuration

ProxyScrape provides **Residential**, **Premium (Datacenter)**, **Dedicated**, and **Mobile** proxies. This section covers the two most common types used with Playwright.

## Quick Reference

| Feature | Residential | Premium Datacenter |
|---------|-------------|-------------------|
| Gateway | `rp.scrapegw.com:6060` | Individual IP:port from list |
| Auth | username:password (dashboard) | username:password (dashboard) |
| Protocols | HTTP, SOCKS5 | HTTP, SOCKS5 |
| Country targeting | `-country-XX` appended to username | Via proxy list selection |
| Sticky sessions | `-session-{id}-lifetime-{min}` appended to username | N/A |

---

## Residential Proxy

ProxyScrape residential proxies use a **gateway** (`rp.scrapegw.com:6060`) with username/password auth from your dashboard.

### Basic Residential

```python
browser = await p.chromium.launch(
    proxy={"server": "http://rp.scrapegw.com:6060"}
)
context = await browser.new_context(
    ignore_https_errors=True,
    http_credentials={
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD",
    }
)
```

### Country Targeting

Append `-country-XX` to your username to target specific countries:

```python
http_credentials = {
    "username": "YOUR_USERNAME-country-in",  # India
    "password": "YOUR_PASSWORD",
}
```

Available country codes include: `-country-us` (USA), `-country-in` (India), `-country-gb` (UK), `-country-de` (Germany), `-country-fr` (France), `-country-jp` (Japan), `-country-au` (Australia), `-country-br` (Brazil), and [many more](https://docs.proxyscrape.com/proxies/rp.scrapegw.com-using-a-specific-country-with-residential-proxies).

### Sticky Sessions

For session persistence (same IP), append session parameters to your username:

```python
# 5-minute sticky session
http_credentials = {
    "username": "YOUR_USERNAME-session-abc123-lifetime-5",
    "password": "YOUR_PASSWORD",
}
```

Combine with country targeting:

```python
http_credentials = {
    "username": "YOUR_USERNAME-country-us-session-abc123-lifetime-10",
    "password": "YOUR_PASSWORD",
}
```

---

## Premium Datacenter Proxy

Premium datacenter proxies use a **proxy list** (individual IP:port pairs from your dashboard), not a single gateway.

```python
# Pick one IP:port from your premium proxy list
browser = await p.chromium.launch(
    proxy={"server": "http://185.199.228.220:7777"}
)
context = await browser.new_context(
    ignore_https_errors=True,
    http_credentials={
        "username": "customer-YOUR_USERNAME",
        "password": "YOUR_PASSWORD",
    }
)
```

> **Note:** The username format is typically `customer-{your_username}` for premium proxies. Check your dashboard for the exact format.

---

# ScrapeOps + Playwright Configuration

ScrapeOps provides an **auto-rotating residential proxy gateway** that returns a fresh residential IP on every request — no IP list management needed.

## Quick Reference

| Feature | Value |
|---------|-------|
| Gateway | `residential-proxy.scrapeops.io:8181` |
| Auth | username:password |
| Auto-rotation | ✅ Every request |
| Protocols | HTTP / HTTPS |
| Country targeting | Via dashboard/API configuration |

## Usage

```python
browser = await p.chromium.launch(
    proxy={"server": "http://residential-proxy.scrapeops.io:8181"}
)
context = await browser.new_context(
    ignore_https_errors=True,
    http_credentials={
        "username": "scrapeops",
        "password": "YOUR_API_KEY",
    }
)
```

## IP Rotation Demo

ScrapeOps rotates IPs automatically — each browser session gets a different residential IP:

```
Request 1: {"ip":"189.203.187.176"}  # Mexico
Request 2: {"ip":"171.225.8.56"}     # Vietnam
Request 3: {"ip":"83.110.143.224"}   # Iran
Request 4: {"ip":"103.35.153.162"}   # Indonesia
Request 5: {"ip":"41.13.182.128"}    # South Africa
```

## Examples

- [`examples/scrapeops_residential.py`](examples/scrapeops_residential.py) — Basic residential proxy
- [`examples/scrapeops_rotation_test.py`](examples/scrapeops_rotation_test.py) — IP rotation demo

---

# Provider Comparison

| Provider | Type | Auto-rotation | Residential IPs | Playwright Support |
|----------|------|---------------|-----------------|-------------------|
| **ScraperAPI** (port) | Gateway (`:8001`) | ✅ | ✅ (premium=true) | ✅ Tested |
| **ScraperAPI** (API) | Endpoint (`api.scraperapi.com`) | ✅ | ✅ (render=true) | ✅ Hybrid (cookie injection) |
| **ProxyScrape Premium** | IP list (individual) | ❌ Manual cycle | ❌ Datacenter only | ✅ Tested |
| **ProxyScrape Residential** | Gateway (`rp.scrapegw.com:6060`) | ✅ | ✅ | ❌ No active sub |
| **ScrapeOps** | Gateway (`residential-proxy.scrapeops.io:8181`) | ✅ | ✅ | ✅ Tested |

---

## Examples

### ScraperAPI
- [`examples/basic_usage.py`](examples/basic_usage.py) — Basic proxy port test
- [`examples/premium_residential.py`](examples/premium_residential.py) — Premium residential India proxy
- [`examples/playwright_integration.py`](examples/playwright_integration.py) — Full Playwright integration
- [`examples/error_handling.py`](examples/error_handling.py) — Retry logic and error handling
- [`examples/api_endpoint_basic.py`](examples/api_endpoint_basic.py) — API endpoint basic usage
- [`examples/api_endpoint_protected_domains.py`](examples/api_endpoint_protected_domains.py) — API endpoint + Playwright hybrid for protected domains

### ProxyScrape
- [`examples/proxyscrape_residential.py`](examples/proxyscrape_residential.py) — ProxyScrape residential basic
- [`examples/proxyscrape_residential_country.py`](examples/proxyscrape_residential_country.py) — ProxyScrape country-targeted
- [`examples/proxyscrape_premium.py`](examples/proxyscrape_premium.py) — ProxyScrape premium datacenter

### ScrapeOps
- [`examples/scrapeops_residential.py`](examples/scrapeops_residential.py) — ScrapeOps residential basic
- [`examples/scrapeops_rotation_test.py`](examples/scrapeops_rotation_test.py) — ScrapeOps IP rotation demo

---

## Requirements

```txt
playwright>=1.40.0
requests>=2.31.0
```

Install:
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## License

MIT

## Contributing

PRs welcome! If you discover additional working configurations or fixes, please open an issue or PR.
