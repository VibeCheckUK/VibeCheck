import requests
from bs4 import BeautifulSoup
from db import get_connection, init_db
import time
import random
from urllib.parse import urljoin

BASE_URL = "https://www.fatsoma.com"

def scrape_fatsoma(city="london", total_events=50):
    """Scrape music events from Fatsoma by city with robust extraction."""
    # Try multiple URL patterns for Fatsoma
    urls_to_try = [
        f"{BASE_URL}/l/gb/{city}",  # New URL structure
        f"{BASE_URL}/{city}/music",  # Original URL structure
        f"{BASE_URL}/discover?location={city}",  # Discovery page
        f"{BASE_URL}/discover"  # General discovery
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }

    print(f"Starting Fatsoma scrape for {city} music events...")
    
    for url in urls_to_try:
        print(f"Trying URL: {url}")
        
        try:
            # Add a small delay to be respectful
            time.sleep(random.uniform(1, 2))
            
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            print(f"✅ Successfully fetched page (content length: {len(resp.text)} chars)")
            
            # Try multiple selectors for Fatsoma event cards
            event_selectors = [
                # Modern Fatsoma selectors (based on typical event site patterns)
                ".event-card", "div.event-card",
                ".event-item", ".event-listing", 
                ".card", ".listing-card",
                "[data-testid*='event']",
                "[class*='event-card']",
                "[class*='event-item']",
                "[class*='listing']",
                # Generic selectors
                ".item", ".tile", ".result",
                "article", "li[class*='event']",
                # Fallback - look for elements with event-related classes
                "[class*='event']"
            ]
            
            cards = []
            selector_used = None
            
            for selector in event_selectors:
                cards = soup.select(selector)
                if cards and len(cards) > 1:  # Need more than 1 to avoid false positives
                    selector_used = selector
                    print(f"✅ Found {len(cards)} event cards using selector: {selector}")
                    break
            
            if not cards:
                print("⚠️ No event cards found with standard selectors, trying content-based search...")
                # Look for any elements that contain event-like content
                all_elements = soup.find_all(text=True)
                event_indicators = [text for text in all_elements if any(word in text.lower() for word in 
                                   ['tickets', 'event', 'music', 'live', 'concert', 'show', 'gig', '£', 'buy now'])]
                
                if event_indicators:
                    print(f"✅ Found {len(event_indicators)} elements with event-related text")
                    # Try to find parent containers of these texts
                    potential_cards = []
                    for text in event_indicators[:10]:  # Check first 10
                        parent = text.parent if hasattr(text, 'parent') else None
                        if parent and parent not in potential_cards:
                            potential_cards.append(parent)
                    cards = potential_cards
                    print(f"✅ Extracted {len(cards)} potential event containers")
                
                if not cards:
                    print("❌ No event content found on this page")
                    # Save HTML for debugging only for the main URL
                    if url == urls_to_try[0]:
                        debug_filename = f"fatsoma_debug_{city}.html"
                        with open(debug_filename, "w", encoding="utf-8") as f:
                            f.write(resp.text)
                        print(f"💾 Saved page HTML to '{debug_filename}' for manual inspection")
                    continue  # Try next URL
            
            # If we found cards, try to extract events
            if cards:
                events = extract_events_from_cards(cards, BASE_URL, total_events)
                if events:
                    print(f"🎯 Fatsoma scraping successful: {len(events)} events extracted from {url}")
                    return events
                else:
                    print(f"⚠️ Found cards but couldn't extract event data from {url}")
                    continue  # Try next URL
            
        except requests.RequestException as e:
            print(f"❌ Request error for {url}: {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error for {url}: {e}")
            continue

    print("❌ All Fatsoma URL attempts failed")
    return []


def extract_events_from_cards(cards, base_url, total_events):
    """Extract events from found cards."""
    events = []
    events_extracted = 0
    
    print(f"🔄 Processing {min(len(cards), total_events)} cards...")
    
    for i, card in enumerate(cards[:total_events]):
        try:
            event_data = extract_fatsoma_event_data(card, base_url)
            if event_data:
                # Check for duplicates
                if not any(existing['url'] == event_data['url'] for existing in events):
                    events.append(event_data)
                    events_extracted += 1
                    print(f"   ✅ {events_extracted}. {event_data['title'][:50]}...")
                    if event_data['date']:
                        print(f"      📅 Date: {event_data['date']}")
                    if event_data['venue']:
                        print(f"      📍 Venue: {event_data['venue'][:40]}...")
                else:
                    print(f"   🔄 Skipping duplicate: {event_data['title'][:40]}...")
            else:
                if i < 3:  # Only show first few failures
                    print(f"   ❌ Failed to extract data from card {i+1}")
                    
        except Exception as e:
            if i < 3:  # Only show first few errors
                print(f"   ❌ Error parsing card {i+1}: {str(e)[:100]}")
            continue

    return events


def extract_fatsoma_event_data(card, base_url):
    """Extract event data from a Fatsoma card element with comprehensive selectors."""
    event_data = {
        "title": None,
        "url": None,
        "date": None,
        "venue": None,
    }
    
    try:
        # Strategy 1: Look for title with multiple approaches
        title_selectors = [
            "h1 a", "h2 a", "h3 a", "h4 a",  # Heading with link
            "h1", "h2", "h3", "h4",  # Just headings
            ".event-title a", ".title a",  # Common class names
            ".event-title", ".title",
            "a[href*='/events/']",  # Link to event page
            "a[href*='/event/']",
            ".event-name", ".name",
            "[data-testid*='title']",
            "[data-testid*='name']"
        ]
        
        title_element = None
        for selector in title_selectors:
            title_element = card.select_one(selector)
            if title_element:
                break
        
        if title_element:
            # Get title text
            title_text = (
                title_element.get("aria-label") or 
                title_element.get("title") or
                title_element.get_text(strip=True)
            )
            if title_text and len(title_text.strip()) > 0:
                event_data["title"] = title_text.strip()
                
                # Try to get URL from title element or find a link in the card
                href = title_element.get("href")
                if not href:
                    # Look for any link in the card
                    link_elem = card.select_one("a[href]")
                    if link_elem:
                        href = link_elem.get("href")
                
                if href:
                    if href.startswith("http"):
                        event_data["url"] = href
                    else:
                        event_data["url"] = urljoin(base_url, href)
        
        # Strategy 2: Look for date with comprehensive selectors
        date_selectors = [
            "time[datetime]",
            "time[content]", 
            "time",
            "[data-testid*='date']",
            "[data-testid*='start']",
            ".event-date", ".date",
            ".event-time", ".time",
            "[class*='date']",
            "[class*='time']",
            "span[aria-label*='date']",
            "div[aria-label*='date']"
        ]
        
        for selector in date_selectors:
            date_elem = card.select_one(selector)
            if date_elem:
                date_text = (
                    date_elem.get("datetime") or 
                    date_elem.get("content") or
                    date_elem.get("aria-label") or
                    date_elem.get_text(strip=True)
                )
                if date_text and len(date_text.strip()) > 2:
                    event_data["date"] = date_text.strip()
                    break
        
        # Strategy 3: Look for venue with comprehensive selectors  
        venue_selectors = [
            "[data-testid*='venue']",
            "[data-testid*='location']",
            "[data-testid*='address']",
            ".venue", ".venue-name",
            ".location", ".address",
            ".event-venue", ".event-location",
            "p.text-sm",  # Original selector
            "p[class*='text']",
            "[class*='venue']",
            "[class*='location']",
            "span[aria-label*='venue']",
            "span[aria-label*='location']",
            "address"
        ]
        
        for selector in venue_selectors:
            venue_elem = card.select_one(selector)
            if venue_elem:
                venue_text = (
                    venue_elem.get("aria-label") or
                    venue_elem.get("title") or
                    venue_elem.get_text(strip=True)
                )
                if venue_text and len(venue_text.strip()) > 2:
                    event_data["venue"] = venue_text.strip()
                    break
        
        # Only return if we have at least title and URL
        if event_data["title"] and event_data["url"]:
            return event_data
        else:
            return None
            
    except Exception as e:
        # Silently fail for individual card extraction errors
        return None


def debug_fatsoma_card(card, card_number=1):
    """Debug function to inspect Fatsoma event card HTML structure."""
    print(f"\n🔍 DEBUG: Inspecting Fatsoma card #{card_number}")
    print("=" * 50)
    
    # Show card HTML structure (truncated)
    card_html = str(card)[:500] + "..." if len(str(card)) > 500 else str(card)
    print(f"Card HTML preview: {card_html}")
    
    # Look for headings that might contain titles
    print("\n📝 Potential title elements:")
    title_elements = card.find_all(["h1", "h2", "h3", "h4", "a"], string=True)
    for i, elem in enumerate(title_elements[:5]):
        text = elem.get_text(strip=True)
        if len(text) > 10:  # Likely to be a title if longer than 10 chars
            print(f"  {i+1}. {elem.name} [{elem.get('class', [])}]: '{text[:60]}...'")
    
    # Look for date elements
    print("\n📅 Potential date elements:")
    date_elements = card.find_all(["time", "span", "div", "p"], string=True)
    for i, elem in enumerate(date_elements[:5]):
        text = elem.get_text(strip=True)
        if any(word in text.lower() for word in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                                                  '2024', '2025', 'today', 'tomorrow', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']):
            print(f"  {i+1}. {elem.name} [{elem.get('class', [])}]: '{text[:50]}...'")
    
    # Look for venue elements
    print("\n📍 Potential venue elements:")
    venue_elements = card.find_all(["span", "div", "p", "address"], string=True)
    for i, elem in enumerate(venue_elements[:5]):
        text = elem.get_text(strip=True)
        if any(word in text.lower() for word in ['london', 'venue', 'street', 'road', 'hall',
                                                  'club', 'bar', 'theatre', 'center', 'centre', 'room']):
            print(f"  {i+1}. {elem.name} [{elem.get('class', [])}]: '{text[:50]}...'")
    
    print("=" * 50)


def scrape_fatsoma_with_debug(city="london", total_events=5):
    """Debug version to inspect HTML structure of Fatsoma cards."""
    url = f"{BASE_URL}/{city}/music"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Try to find event cards
    cards = soup.select("div.event-card")
    if not cards:
        cards = soup.select(".event-card")
    if not cards:
        cards = soup.select("[class*='event']")
    
    print(f"Found {len(cards)} potential event cards")
    
    if not cards:
        print("No cards found - saving full HTML for inspection")
        with open("fatsoma_full_debug.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        return
    
    # Debug first 3 cards
    for i, card in enumerate(cards[:3]):
        debug_fatsoma_card(card, i+1)
        
        # Try to extract with current logic
        event_data = extract_fatsoma_event_data(card, BASE_URL)
        if event_data:
            print(f"\n✅ Current extraction result:")
            print(f"   Title: {event_data['title']}")
            print(f"   Date: {event_data['date'] or 'NOT FOUND'}")
            print(f"   Venue: {event_data['venue'] or 'NOT FOUND'}")
            print(f"   URL: {event_data['url']}")
        else:
            print(f"\n❌ Current extraction failed")


def store_events(events):
    """Save Fatsoma events into SQLite DB with better error handling."""
    if not events:
        print("No Fatsoma events to store")
        return
        
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    stored_count = 0
    for e in events:
        try:
            cur.execute("""
                INSERT OR REPLACE INTO events (id, name, url, date, genre, subgenre, venue_city)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                e["url"],  # use URL as unique ID
                e["title"],
                e["url"],
                e["date"],
                "music",  # default genre instead of None
                None,     # subgenre placeholder
                e["venue"],
            ))
            stored_count += 1
        except Exception as e:
            print(f"Error storing Fatsoma event: {e}")

    conn.commit()
    conn.close()
    print(f"Stored {stored_count} Fatsoma events in database")


# Test function for debugging
if __name__ == "__main__":
    print("🔍 Running Fatsoma debug version to inspect HTML structure...")
    scrape_fatsoma_with_debug()
    
    print("\n" + "="*50)
    print("🔄 Now trying normal scraping...")
    events = scrape_fatsoma(city="london", total_events=10)
    
    if events:
        print(f"\n📋 Sample of {len(events)} events found:")
        for i, event in enumerate(events[:3]):
            print(f"{i+1}. {event['title']}")
            print(f"   📅 {event.get('date', 'No date')}")
            print(f"   📍 {event.get('venue', 'No venue')}")
            print(f"   🔗 {event['url']}")
            print()
        
        store_events(events)
    else:
        print("❌ No events extracted. Check the debug output above.")