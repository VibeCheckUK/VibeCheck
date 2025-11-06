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

# in-memory cache
CACHE = {
    "event_ids": set(),
    "events": {}
}

def build_eventbrite_filters(budget, when):
    params = []
    
    if when == "tonight":
        params.append("date=today")
    elif when == "weekend":
        params.append("date=this_weekend")
    elif when == "week":
        params.append("date=this_week")
    elif when == "month":
        params.append("date=this_month")
    
    if budget == "free":
        params.append("price=free")
    
    if not params:
        return ""
    
    return "?" + "&".join(params)


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
    
    # --- 1. THIS IS THE FIX ---
    # Get the 'is_free' boolean from the API
    is_free = data.get("is_free", False) 
    # --- END FIX ---

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

    # --- 2. THIS IS THE FIX ---
    # Store 'is_free' in the event info
    event_info = {"title": title, "date": start_date, "venue": venue, "url": event_url, "is_free": is_free}
    CACHE["events"][event_id] = event_info
    return event_info


async def scrape_keyword(session, city, keyword, max_events_per_keyword=10, max_pages=1, budget="any", when="any"):
    """Scrape a single keyword across multiple pages."""
    results = []
    keyword_url_part = quote(keyword.lower().replace(" ", "-"))
    
    filter_params = build_eventbrite_filters(budget, when)
    
    base_search_url = f"{BASE_URL}/d/united-kingdom--{city}/{keyword_url_part}/{filter_params}"

    print(f"\n🔎 Searching Eventbrite for keyword: '{keyword}' in {city} ({base_search_url})")

    for page in range(1, max_pages + 1):
        page_param = f"&page={page}" if filter_params else f"?page={page}"
        page_url = f"{base_search_url}{page_param}"
        
        html = await fetch(session, page_url)
        if not html:
            break

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

        tasks = [
            fetch_event_api(session, eid)
            for eid in list(event_ids)[:max_events_per_keyword]
        ]
        details = await asyncio.gather(*tasks)

        for r in details:
            if r:
                # --- 3. THIS IS THE FIX ---
                # Check the 'is_free' flag before adding the event
                if budget == "free" and not r.get("is_free", False):
                    print(f"   FILTERED (Not Free): {r['title']}")
                    continue # Skip this event because user wants 'free' and it's not
                # --- END FIX ---

                results.append(r)
                print(f"   ✅ {r['title']} | {r.get('date','TBA')} | {r.get('venue','TBA')}")

    return results


async def scrape_eventbrite_async(city="london", keywords=None, max_events_per_keyword=10, max_pages=1, budget="any", when="any"):
    if not keywords:
        return []

    async with aiohttp.ClientSession() as session:
        tasks = [
            scrape_keyword(session, city, kw, max_events_per_keyword, max_pages, budget, when)
            for kw in keywords
        ]
        results = await asyncio.gather(*tasks)

    all_events = [event for sublist in results for event in sublist]
    print(f"\n🏁 Eventbrite scraping complete: {len(all_events)} unique events extracted")
    return all_events


def scrape_eventbrite(*args, **kwargs):
    """Sync wrapper"""
    return asyncio.run(scrape_eventbrite_async(*args, **kwargs))