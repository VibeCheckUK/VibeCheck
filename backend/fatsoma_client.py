# fatsoma_client.py
import asyncio
from playwright.async_api import async_playwright
from db import store_event


async def scrape_fatsoma_async(keywords=None, city="london", max_events_per_keyword=10, headless=True):
    """Scrape Fatsoma events by keywords using Playwright (async)."""
    if not keywords:
        return []

    all_events = []
    seen_urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        for keyword in keywords:
            url = f"https://www.fatsoma.com/search?query={keyword}&location={city}"
            print(f"\n🔎 Searching Fatsoma for keyword: '{keyword}' ({url})")

            try:
                await page.goto(url, timeout=20000)
                await page.wait_for_selector("a[href*='/e/']", timeout=10000)
            except Exception:
                print("   ⚠️ No events loaded for this keyword")
                continue

            event_links = await page.query_selector_all("a[href*='/e/']")
            keyword_events = []

            for link in event_links[:max_events_per_keyword]:
                href = await link.get_attribute("href")
                text = (await link.inner_text()).strip()

                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                event = {
                    "title": text or "Untitled Event",
                    "url": href,
                    "date": None,
                    "venue": None,
                }

                keyword_events.append(event)
                store_event(event)

            if keyword_events:
                all_events.extend(keyword_events)
                print(f"   ✅ Found {len(keyword_events)} Fatsoma events")
            else:
                print("   ⚠️ No Fatsoma events found")

        await browser.close()

    print(f"\n🏁 Fatsoma scraping complete: {len(all_events)} unique events extracted")
    return all_events


def scrape_fatsoma(*args, **kwargs):
    """Sync wrapper for run.py"""
    return asyncio.run(scrape_fatsoma_async(*args, **kwargs))
