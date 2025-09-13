# eventbrite_client.py
import asyncio
import aiohttp
import json
from urllib.parse import urljoin, quote

EVENTBRITE_TOKEN = "EXRFYBNSCU35EOEJ25NU"
BASE_URL = "https://www.eventbrite.co.uk"
API_BASE = "https://www.eventbriteapi.com/v3/events/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/100.0.4896.127 Safari/537.36"
    )
}

# in-memory cache to avoid duplicate lookups
CACHE = {
    "event_ids": set(),
    "events": {}
}


async def fetch(session, url, headers=None, return_json=False):
    try:
        async with session.get(url, headers=headers or HEADERS, timeout=15) as resp:
            if resp.status == 200:
                return await resp.json() if return_json else await resp.text()
            else:
                print(f"    ❌ HTTP {resp.status} for {url}")
    except Exception as e:
        print(f"    ❌ Request error for {url}: {e}")
    return None


async def fetch_event_api(session, event_id):
    """Fetch full event details from Eventbrite API (with caching)."""
    if event_id in CACHE["events"]:
        return CACHE["events"][event_id]

    url = f"{API_BASE}{event_id}/?token={EVENTBRITE_TOKEN}"
    data = await fetch(session, url, return_json=True)
    if not data:
        return None

    title = data.get("name", {}).get("text")
    start_date = data.get("start", {}).get("local")
    venue = None
    event_url = data.get("url")
    venue_id = data.get("venue_id")

    if venue_id:
        venue_data = await fetch(
            session,
            f"https://www.eventbriteapi.com/v3/venues/{venue_id}/?token={EVENTBRITE_TOKEN}",
            return_json=True,
        )
        if venue_data:
            venue = venue_data.get("name")

    event_info = {"title": title, "date": start_date, "venue": venue, "url": event_url}
    CACHE["events"][event_id] = event_info
    return event_info


async def scrape_keyword(session, city, keyword, max_events_per_keyword=10, max_pages=1):
    """Scrape a single keyword across multiple pages."""
    results = []
    keyword_url_part = quote(keyword.lower().replace(" ", "-"))
    base_search_url = f"{BASE_URL}/d/united-kingdom--{city}/{keyword_url_part}/"

    print(f"\n🔎 Searching Eventbrite for keyword: '{keyword}' in {city}")

    for page in range(1, max_pages + 1):
        page_url = f"{base_search_url}?page={page}"
        html = await fetch(session, page_url)
        if not html:
            break

        # Extract event IDs
        event_ids = set()
        start = 0
        while True:
            idx = html.find('data-event-id="', start)
            if idx == -1:
                break
            start = idx + len('data-event-id="')
            end_idx = html.find('"', start)
            event_id = html[start:end_idx].strip()
            if event_id and event_id not in CACHE["event_ids"]:
                CACHE["event_ids"].add(event_id)
                event_ids.add(event_id)
            start = end_idx

        if not event_ids:
            break

        # Fetch event details concurrently
        tasks = [
            fetch_event_api(session, eid)
            for eid in list(event_ids)[:max_events_per_keyword]
        ]
        details = await asyncio.gather(*tasks)

        for r in details:
            if r:
                results.append(r)
                print(f"   ✅ {r['title']} | {r.get('date','TBA')} | {r.get('venue','TBA')}")

    return results


async def scrape_eventbrite_async(city="london", keywords=None, max_events_per_keyword=10, max_pages=1):
    if not keywords:
        return []

    async with aiohttp.ClientSession() as session:
        tasks = [
            scrape_keyword(session, city, kw, max_events_per_keyword, max_pages)
            for kw in keywords
        ]
        results = await asyncio.gather(*tasks)

    # flatten
    all_events = [event for sublist in results for event in sublist]
    print(f"\n🏁 Eventbrite scraping complete: {len(all_events)} unique events extracted")
    return all_events


def scrape_eventbrite(*args, **kwargs):
    """Sync wrapper"""
    return asyncio.run(scrape_eventbrite_async(*args, **kwargs))
