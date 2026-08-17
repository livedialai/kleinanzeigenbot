#!/usr/bin/env python3
"""
List all active Kleinanzeigen ads for the logged-in account.
Reuses session cookies from /tmp/chrome-data (from previous bot login).

Usage:
    source venv/bin/activate
    xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
        python list_ads.py

Prerequisites:
    - SSH SOCKS proxy running: ssh -R 1080 root@<server> (from home PC)
    - Bot has logged in at least once (cookies in /tmp/chrome-data)
"""
import asyncio
import json
import nodriver
from nodriver.core.config import Config


async def main():
    cfg = Config(
        headless=False,
        browser_executable_path="/usr/bin/chromium",
        browser_args=[
            "--no-sandbox", "--disable-gpu",
            "--proxy-server=socks5://127.0.0.1:1080",
            "--user-data-dir=/tmp/chrome-data",
        ],
    )
    cfg.sandbox = False
    browser = await nodriver.start(cfg)

    # Open "Meine Anzeigen" page (session cookies from previous login)
    page = await browser.get("https://www.kleinanzeigen.de/m-meine-anzeigen.html")
    await asyncio.sleep(8)

    url = await page.evaluate("window.location.href")
    if "login" in url.lower():
        print("ERROR: Not logged in. Run the bot first to establish a session:")
        print("  xvfb-run --auto-servernum python -m kleinanzeigen_bot publish --ads=all")
        browser.stop()
        return

    # Scrape ads from the DOM (the JSON API is unreliable via fetch)
    ads = await page.evaluate("""
        (() => {
            const items = document.querySelectorAll('[data-testid="ad-item"], .aditem, [class*="AdItem"]');
            const results = [];
            
            // Try multiple selectors since the DOM structure changes
            const cards = document.querySelectorAll('article, [class*="ad-card"], [class*="AdCard"]');
            for (const card of cards) {
                const title = card.querySelector('h2, h3, [class*="title"], a[href*="/s-anzeige"]');
                const price = card.querySelector('[class*="price"], [class*="Price"]');
                const link = card.querySelector('a[href*="/s-anzeige"]');
                results.push({
                    title: title ? title.textContent.trim() : '?',
                    price: price ? price.textContent.trim() : '?',
                    url: link ? link.href : '',
                });
            }
            
            // Fallback: get all text from the main content
            if (results.length === 0) {
                return JSON.stringify({
                    error: "No structured ads found",
                    body_text: document.body.innerText.substring(0, 10000)
                });
            }
            return JSON.stringify(results);
        })()
    """)

    try:
        data = json.loads(ads)
        if isinstance(data, dict) and "error" in data:
            print(f"Could not parse structured ads. Raw page text:\n")
            print(data.get("body_text", "")[:5000])
        elif isinstance(data, list):
            print(f"\n=== {len(data)} Anzeigen gefunden ===\n")
            for i, ad in enumerate(data, 1):
                print(f"  {i}. {ad.get('title', '?')}")
                print(f"     Preis: {ad.get('price', '?')}")
                if ad.get("url"):
                    print(f"     URL: {ad['url']}")
                print()
    except (json.JSONDecodeError, TypeError):
        print(f"Raw output: {ads}")

    browser.stop()

asyncio.run(main())
