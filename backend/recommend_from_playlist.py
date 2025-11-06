# recommend_from_playlist.py
from spotify_client import extract_playlist_profile
from eventbrite_client import scrape_eventbrite

def recommend_events_from_playlist(playlist_id, city="london"):
    """
    Combines Spotify + Eventbrite:
    - Extracts genres from a playlist
    - Searches for related events in Eventbrite
    - Returns event recommendations
    """
    print("\n🎧 Extracting playlist profile...")
    profile = extract_playlist_profile(playlist_id)
    genres = profile.get("genres", [])
    if not genres:
        print("❌ No genres found in playlist.")
        return []

    # Pick top 3 genres for search
    search_genres = genres[:3]
    print(f"🎯 Searching events for genres: {search_genres}")

    # Scrape Eventbrite using the genres as keywords
    events = scrape_eventbrite(city=city, keywords=search_genres, max_events_per_keyword=5)

    print("\n✅ Final Recommended Events:")
    for ev in events[:10]:
        print(f" - {ev['title']} ({ev.get('venue','TBA')}) → {ev['url']}")
    return events

if __name__ == "__main__":
    playlist_id = "37i9dQZF1DXcBWIGoYBM5M"  # Spotify's "Today's Top Hits"
    recommend_events_from_playlist(playlist_id, city="london")

