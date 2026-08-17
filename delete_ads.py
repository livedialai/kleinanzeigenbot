import asyncio
import json
import nodriver
from nodriver.core.config import Config

async def main():
    cfg = Config(
        headless=False,
        browser_executable_path="/usr/bin/chromium",
        browser_args=["--no-sandbox", "--disable-gpu",
                       "--proxy-server=socks5://127.0.0.1:1080",
                       "--user-data-dir=/tmp/chrome-data"],
    )
    cfg.sandbox = False
    browser = await nodriver.start(cfg)

    # Step 1: Open "Meine Anzeigen" to get CSRF token
    page = await browser.get("https://www.kleinanzeigen.de/m-meine-anzeigen.html")
    await asyncio.sleep(10)

    url = await page.evaluate("window.location.href")
    if "login" in url.lower():
        print("ERROR: Not logged in.")
        browser.stop()
        return

    # Get CSRF token
    csrf = await page.evaluate("""
        (document.querySelector('meta[name="_csrf"]')?.content || 
         document.querySelector('meta[name="csrf-token"]')?.content) || null
    """)
    if not csrf:
        print("ERROR: No CSRF token found")
        browser.stop()
        return
    print(f"CSRF token: {csrf[:20]}...")

    # Step 2: Navigate to JSON API to get ad IDs
    print("Fetching ads...")
    page2 = await browser.get("https://www.kleinanzeigen.de/m-meine-anzeigen-verwalten.json?sort=DEFAULT")
    await asyncio.sleep(5)
    json_text = await page2.evaluate("document.body.innerText")

    data = json.loads(json_text)
    ads = data.get("ads", [])
    print(f"\n{len(ads)} Anzeigen gefunden:\n")
    for ad in ads:
        print(f"  [{ad['id']}] {ad['title']}")

    # Step 3: Delete each ad
    print(f"\nLösche {len(ads)} Anzeigen...\n")
    for ad in ads:
        ad_id = ad["id"]
        title = ad["title"]
        print(f"  Lösche [{ad_id}] {title}...")

        # Use fetch from the page context with CSRF
        result = await page2.evaluate(f"""
            (async () => {{
                try {{
                    const resp = await fetch('https://www.kleinanzeigen.de/m-anzeigen-loeschen.json?ids={ad_id}', {{
                        method: 'POST',
                        credentials: 'include',
                        headers: {{
                            'x-csrf-token': '{csrf}',
                        }}
                    }});
                    return 'HTTP ' + resp.status + ': ' + resp.statusText;
                }} catch(e) {{
                    return 'ERROR: ' + e.message;
                }}
            }})()
        """)
        print(f"    -> {result}")
        await asyncio.sleep(2)

    # Step 4: Verify deletion
    print("\nVerifikation...")
    page3 = await browser.get("https://www.kleinanzeigen.de/m-meine-anzeigen-verwalten.json?sort=DEFAULT")
    await asyncio.sleep(5)
    verify_text = await page3.evaluate("document.body.innerText")
    verify_data = json.loads(verify_text)
    remaining = len(verify_data.get("ads", []))
    print(f"\n=== {remaining} Anzeigen verbleibend ===")

    browser.stop()

asyncio.run(main())
