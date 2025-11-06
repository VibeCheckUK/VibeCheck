# fatsoma_client.py
import asyncio
from playwright.async_api import async_playwright
from db import store_event

FATSOMA_BASE_URL = "https://www.fatsoma.com"

# --- NEW: Helper function to build filter query string ---
def build_fatsoma_filters(budget, when):
    params = []
    
    # 1. 'when' filter
    # (REMOVED - Fatsoma's URL parameters for this are unknown and were not working)
    
    # 2. 'budget' filter
    # (REMOVED - Price ranges are not supported by Fatsoma's search URL)
    # We will ONLY keep the 'free' filter, as it is standard.
    if budget == "free":
        params.append("price=free")
    
    if not params:
        return ""
    
    return "&" + "&".join(params)
# --- End of new function ---


# --- Update function signature to accept new args ---
async def scrape_fatsoma_async(keywords=None, city="london", max_events_per_keyword=10, headless=True, budget="any", when="any"):
    """Scrape Fatsoma events by keywords using Playwright (async)."""
    if not keywords:
        return []

    all_events = []
    seen_urls = set()

    # --- Build filters ONCE ---
    # This will now only add '&price=free' if selected, and nothing else.
    filter_params = build_fatsoma_filters(budget, when)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        for keyword in keywords:
            # --- Add filter_params to the URL ---
            url = f"{FATSOMA_BASE_URL}/search?query={keyword}&location={city}{filter_params}"
            
            print(f"\n🔎 Searching Fatsoma for keyword: '{keyword}' ({url})")

            try:
                await page.goto(url, timeout=20000)
                await page.wait_for_selector("a[href*='/e/']", timeout=10000)
            except Exception:
                print("   ⚠️ No events loaded for this keyword or filters")
                continue

            event_links = await page.query_selector_all("a[href*='/e/']")
            keyword_events = []

            for link in event_links[:max_events_per_keyword]:
                parent_card = await link.query_selector('xpath=..')
                if not parent_card:
                    continue 

                full_text = (await parent_card.inner_text()).strip()
                relative_href = await link.get_attribute("href")

                if not relative_href:
                    continue
                
                absolute_url = f"{FATSOMA_BASE_URL}{relative_href}"
                
                if absolute_url in seen_urls:
                    continue
                seen_urls.add(absolute_url)

                title = "Untitled Event"
                date = "TBA"
                venue = "TBA"

                if full_text:
                    parts = full_text.split('\n')
                    if len(parts) > 0:
                        title = parts[0].strip()
                    if len(parts) > 1:
                        date = parts[1].strip()
                    if len(parts) > 2:
                        venue = parts[2].strip()

                event = {
                    "title": title,
                    "url": absolute_url,
                    "date": date,
                    "venue": venue,
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