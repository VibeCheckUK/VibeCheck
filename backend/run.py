from spotify_client import extract_playlist_profile
from fatsoma_client import scrape_fatsoma, store_events
from eventbrite_client import scrape_eventbrite, store_eventbrite_events
from matcher import match_events_to_profile, print_match_details

def main():
    # You can change this to any playlist ID
    playlist_id = "15TxeE5tqTv0TgS1j4p2pQ"  # Tamil playlist
    # playlist_id = "37i9dQZF1DX0XUsuxWHRQd"  # Popular mainstream playlist (for testing)
    
    print("🎵 Starting VibeCheck Event Matcher...")
    print("=" * 50)
    
    # Step 1: Extract Spotify profile
    print("1️⃣ Fetching Spotify profile...")
    try:
        profile = extract_playlist_profile(playlist_id)
        print(f"✅ Profile extracted: {profile['total_artists']} artists, {len(profile['genres'])} genres")
        print(f"   Sample genres: {profile['genres'][:5]}...")
        print(f"   Sample artists: {profile['artists'][:5]}...")
    except Exception as e:
        print(f"❌ Error extracting Spotify profile: {e}")
        return
    
    # Step 2: Scrape events from multiple sources
    print("\n2️⃣ Scraping events from multiple sources...")
    all_events = []
    
    # Scrape Fatsoma
    print("   📅 Scraping Fatsoma...")
    try:
        fatsoma_events = scrape_fatsoma(city="london", total_events=25)
        if fatsoma_events:
            all_events.extend(fatsoma_events)
            store_events(fatsoma_events)
            print(f"   ✅ Found {len(fatsoma_events)} Fatsoma events")
        else:
            print("   ⚠️ No Fatsoma events found")
    except Exception as e:
        print(f"   ❌ Error scraping Fatsoma: {e}")
    
    # Scrape Eventbrite
    print("   📅 Scraping Eventbrite...")
    try:
        eventbrite_events = scrape_eventbrite(city="london", category="music", total_events=25)
        if eventbrite_events:
            all_events.extend(eventbrite_events)
            store_eventbrite_events(eventbrite_events)
            print(f"   ✅ Found {len(eventbrite_events)} Eventbrite events")
        else:
            print("   ⚠️ No Eventbrite events found")
    except Exception as e:
        print(f"   ❌ Error scraping Eventbrite: {e}")
    
    print(f"\n📊 Total events scraped: {len(all_events)}")
    
    if not all_events:
        print("❌ No events found from any source. Please check the scrapers.")
        return
    
    # Step 3: Match events to profile
    print("\n3️⃣ Matching events to your music profile...")
    try:
        matches = match_events_to_profile(all_events, profile)
        
        if matches:
            print(f"✅ Found {len(matches)} matching events!")
            
            # Print top recommendations
            print("\n🔥 TOP RECOMMENDED EVENTS:")
            print("=" * 50)
            
            for i, match in enumerate(matches[:10]):
                event = match["event"]
                score = match["score"]
                keywords = match.get("matched_keywords", [])
                
                print(f"\n{i+1}. {event['title']}")
                print(f"   📅 Date: {event.get('date', 'TBA')}")
                print(f"   📍 Venue: {event.get('venue', 'TBA')}")
                print(f"   🎯 Match Score: {score}")
                if keywords:
                    print(f"   🏷️ Matched: {', '.join(keywords[:3])}...")
                print(f"   🔗 {event['url']}")
            
            # Print detailed match analysis for debugging
            if len(matches) > 0:
                print_match_details(matches, limit=3)
                
        else:
            print("❌ No matching events found.")
            print("💡 Try using a more mainstream playlist or different city.")
            
            # Show some sample events for debugging
            print(f"\n📋 Sample events found (first 5 of {len(all_events)}):")
            for i, event in enumerate(all_events[:5]):
                print(f"   {i+1}. {event['title']} @ {event.get('venue', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ Error during matching: {e}")
    
    print("\n✨ VibeCheck complete!")


if __name__ == "__main__":
    main()
