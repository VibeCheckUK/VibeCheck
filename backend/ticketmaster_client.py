import requests
from db import get_connection, init_db
from config import TICKETMASTER_KEY

def fetch_uk_events():
    """Fetch MUSIC events in the UK from Ticketmaster API."""
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TICKETMASTER_KEY, 
        "countryCode": "GB", 
        "size": 50,
        "classificationName": "Music"  # This filters for music events only!
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("_embedded", {}).get("events", [])

def fetch_uk_events_multiple_pages(total_events=200):
    """Fetch more music events with pagination for better variety."""
    all_events = []
    page = 0
    events_per_page = 50
    
    while len(all_events) < total_events:
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            "apikey": TICKETMASTER_KEY,
            "countryCode": "GB",
            "size": events_per_page,
            "classificationName": "Music",
            "page": page
        }
        
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            events = data.get("_embedded", {}).get("events", [])
            if not events:  # No more events
                break
                
            all_events.extend(events)
            page += 1
            
            print(f"Fetched page {page}, total events: {len(all_events)}")
            
        except requests.exceptions.HTTPError as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    return all_events[:total_events]  # Return only the requested number

def store_events(events):
    """Save Ticketmaster events into SQLite DB."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    
    music_events_count = 0
    
    for e in events:
        # Extract genre info
        classifications = e.get("classifications", [{}])
        genre = classifications[0].get("genre", {}).get("name") if classifications else None
        subgenre = classifications[0].get("subGenre", {}).get("name") if classifications else None
        
        # Extract venue info
        venues = e.get("_embedded", {}).get("venues", [{}])
        city = venues[0].get("city", {}).get("name") if venues else None
        
        # Extract date
        date = e.get("dates", {}).get("start", {}).get("localDate")
        
        cur.execute("""
            INSERT OR REPLACE INTO events (id, name, url, date, genre, subgenre, venue_city)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            e["id"],
            e.get("name"),
            e.get("url"),
            date,
            genre,
            subgenre,
            city,
        ))
        
        if genre:  # Count actual music events
            music_events_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Stored {len(events)} total events, {music_events_count} with genre info")
