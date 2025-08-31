import requests
from bs4 import BeautifulSoup
from db import get_connection, init_db
import time
import random
from urllib.parse import urljoin

BASE_URL = "https://www.eventbrite.co.uk"

def scrape_eventbrite(city="london", category="music", total_events=50):
    """Scrape music events from Eventbrite by city using web scraping only."""
    # Eventbrite search URL structure
    url = f"{BASE_URL}/d/{city}/{category}/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    events = []
    page = 1
    max_pages = 3  # Hard limit to prevent infinite loops
    
    print(f"Starting Eventbrite scrape for {city} {category} events...")
    
    while len(events) < total_events and page <= max_pages:
        try:
            # Add page parameter for pagination
            page_url = f"{url}?page={page}"
            print(f"Scraping page {page}/{max_pages}: {page_url}")
            
            # Add random delay to avoid being blocked
            time.sleep(random.uniform(1, 2))
            
            resp = requests.get(page_url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try multiple selectors for Eventbrite events
            event_selectors = [
                ".event-card",
                "[data-testid='search-result-event-item']", 
                ".search-event-card-wrapper",
                "[data-testid='search-event-card']",
                ".search-result-event-listing",
                ".event-card-wrapper"
            ]
            
            page_events = []
            selector_used = None
            
            for selector in event_selectors:
                page_events = soup.select(selector)
                if page_events:
                    selector_used = selector
                    print(f"   Found {len(page_events)} event cards using selector: {selector}")
                    break
            
            if not page_events:
                print("   No event cards found with any selector, trying fallback...")
                # Fallback: look for any div with 'event' in class name
                all_divs = soup.find_all("div", class_=True)
                page_events = [div for div in all_divs if any('event' in cls.lower() for cls in div.get('class', []))]
                if page_events:
                    print(f"   Fallback found {len(page_events)} potential event divs")
                else:
                    print("   No events found on this page, stopping pagination")
                    break
            
            # Track how many events we successfully extract from this page
            events_extracted_this_page = 0
            
            for i, card in enumerate(page_events):
                if len(events) >= total_events:
                    break
                    
                try:
                    event_data = extract_event_data(card, BASE_URL)
                    if event_data:
                        # Check for duplicates before adding
                        if not any(existing['url'] == event_data['url'] for existing in events):
                            events.append(event_data)
                            events_extracted_this_page += 1
                            print(f"   ✅ Extracted: {event_data['title'][:50]}...")
                            if event_data['date']:
                                print(f"      📅 Date: {event_data['date']}")
                            if event_data['venue']:
                                print(f"      📍 Venue: {event_data['venue'][:40]}...")
                        else:
                            print(f"   🔄 Skipping duplicate: {event_data['title'][:40]}...")
                    else:
                        if i < 3:  # Only show first few failures to avoid spam
                            print(f"   ❌ Failed to extract data from card {i+1}")
                    
                except Exception as e:
                    if i < 3:  # Only show first few errors
                        print(f"   ❌ Error parsing card {i+1}: {str(e)[:100]}")
                    continue
            
            print(f"   📊 Page {page} summary: Found {len(page_events)} cards, extracted {events_extracted_this_page} events")
            
            # Stop if we're not extracting any events despite finding cards
            if len(page_events) > 10 and events_extracted_this_page == 0:
                print("   ⚠️ Found many cards but extracted 0 events - extraction logic may be broken")
                break
            
            # Stop if no cards found
            if len(page_events) == 0:
                print("   ⚠️ No more event cards found, stopping pagination")
                break
                
            page += 1
            
        except requests.RequestException as e:
            print(f"   ❌ Request error on page {page}: {e}")
            break
        except Exception as e:
            print(f"   ❌ Unexpected error on page {page}: {e}")
            break

    print(f"🎯 Eventbrite scraping complete: {len(events)} events extracted from {page-1} pages")
    return events


def extract_event_data(card, base_url):
    """Extract event data from a card element with improved error handling."""
    event_data = {
        "title": None,
        "url": None,
        "date": None,
        "venue": None,
    }
    
    try:
        # Strategy 1: Look for title with multiple approaches
        title_selectors = [
            "h3 a[aria-label]",  # Most specific first
            "h3 a", 
            "h2 a",
            "h1 a",
            "[data-testid*='title'] a",
            ".event-card__title a",
            ".search-event-card-title a",
            "a[href*='/e/']",  # Any link to an event page
        ]
        
        title_element = None
        for selector in title_selectors:
            title_element = card.select_one(selector)
            if title_element:
                break
        
        # If still no title element, try getting any link
        if not title_element:
            title_element = card.select_one("a[href]")
        
        if title_element:
            # Get title from aria-label first, then text content
            title_text = (
                title_element.get("aria-label") or 
                title_element.get_text(strip=True)
            )
            if title_text and len(title_text.strip()) > 0:
                event_data["title"] = title_text.strip()
                
                # Get URL from the same element
                href = title_element.get("href")
                if href:
                    if href.startswith("http"):
                        event_data["url"] = href
                    else:
                        event_data["url"] = urljoin(base_url, href)
        
        # Strategy 2: Look for date information
        date_selectors = [
            "time[datetime]",
            "time",
            "[data-testid*='date']",
            ".event-card__date",
            ".search-event-card-date",
            ".event-date"
        ]
        
        for selector in date_selectors:
            date_elem = card.select_one(selector)
            if date_elem:
                date_text = (
                    date_elem.get("datetime") or 
                    date_elem.get("content") or
                    date_elem.get_text(strip=True)
                )
                if date_text:
                    event_data["date"] = date_text.strip()
                    break
        
        # Strategy 3: Look for venue information
        venue_selectors = [
            "[data-testid*='location']",
            "[data-testid*='venue']", 
            ".event-card__location",
            ".search-event-card-location",
            ".venue-name",
            ".event-venue"
        ]
        
        for selector in venue_selectors:
            venue_elem = card.select_one(selector)
            if venue_elem:
                venue_text = venue_elem.get_text(strip=True)
                if venue_text:
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


def store_eventbrite_events(events):
    """Save Eventbrite events into SQLite DB."""
    if not events:
        print("No Eventbrite events to store")
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
                "music",  # default genre
                None,     # subgenre placeholder
                e["venue"],
            ))
            stored_count += 1
        except Exception as e:
            print(f"Error storing event: {e}")

    conn.commit()
    conn.close()
    print(f"Stored {stored_count} Eventbrite events in database")


def debug_event_card(card, card_number=1):
    """Debug function to inspect event card HTML structure."""
    print(f"\n🔍 DEBUG: Inspecting event card #{card_number}")
    print("=" * 50)
    
    # Show card HTML structure (truncated)
    card_html = str(card)[:500] + "..." if len(str(card)) > 500 else str(card)
    print(f"Card HTML preview: {card_html}")
    
    # Look for any elements that might contain date
    print("\n📅 Potential date elements:")
    date_elements = card.find_all(["time", "span", "div", "p"], string=True)
    for i, elem in enumerate(date_elements[:5]):  # Show first 5
        text = elem.get_text(strip=True)
        if any(word in text.lower() for word in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                                                  '2024', '2025', 'today', 'tomorrow']):
            print(f"  {i+1}. {elem.name} [{elem.get('class', [])}]: '{text[:50]}...'")
    
    # Look for any elements that might contain venue
    print("\n📍 Potential venue elements:")
    venue_elements = card.find_all(["span", "div", "p", "address"], string=True)
    for i, elem in enumerate(venue_elements[:5]):  # Show first 5
        text = elem.get_text(strip=True)
        if any(word in text.lower() for word in ['london', 'venue', 'street', 'road', 'hall',
                                                  'club', 'bar', 'theatre', 'center', 'centre']):
            print(f"  {i+1}. {elem.name} [{elem.get('class', [])}]: '{text[:50]}...'")
    
    print("=" * 50)


def scrape_eventbrite_with_debug(city="london", category="music", total_events=5):
    """Debug version that shows HTML structure of first few cards."""
    url = f"{BASE_URL}/d/{city}/{category}/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    page_events = soup.select(".event-card")
    print(f"Found {len(page_events)} event cards")
    
    # Debug first 3 cards
    for i, card in enumerate(page_events[:3]):
        debug_event_card(card, i+1)
        
        # Try to extract with current logic
        event_data = extract_event_data(card, BASE_URL)
        if event_data:
            print(f"\n✅ Current extraction result:")
            print(f"   Title: {event_data['title']}")
            print(f"   Date: {event_data['date'] or 'NOT FOUND'}")
            print(f"   Venue: {event_data['venue'] or 'NOT FOUND'}")
            print(f"   URL: {event_data['url']}")
        else:
            print(f"\n❌ Current extraction failed")


# Test function for debugging
if __name__ == "__main__":
    print("🔍 Running debug version to inspect HTML structure...")
    scrape_eventbrite_with_debug()
