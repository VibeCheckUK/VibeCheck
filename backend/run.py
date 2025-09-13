# run.py
import argparse
import asyncio
import json
import sys
import time
from keyword_ranker import rank_genres

try:
    from spotify_client import extract_playlist_profile
    from fatsoma_client import scrape_fatsoma_async
    from eventbrite_client import scrape_eventbrite_async
    from matcher import match_events_to_profile, print_match_details
except Exception as e:
    print("Error importing project modules:", e)
    raise


def event_matches_city(event: dict, city: str) -> bool:
    """Check if event mentions the city (loose match)."""
    if not city:
        return True
    city = city.strip().lower()
    try:
        j = json.dumps(event).lower()
    except Exception:
        j = str(event).lower()

    if city in j:
        return True
    if city == "london":
        boroughs = [
            "shoreditch",
            "camden",
            "brixton",
            "hackney",
            "soho",
            "islington",
            "elephant",
            "clapham",
            "southwark",
            "westminster",
        ]
        return any(b in j for b in boroughs)

    return False


async def main_async(playlist_id, city, top_n):
    print("🎵 Starting VibeCheck Event Matcher...")
    print("=" * 50)
    start_total = time.time()

    # 1️⃣ Spotify profile
    print("1️⃣ Fetching Spotify profile...")
    t0 = time.time()
    try:
        profile = extract_playlist_profile(playlist_id)
        print(
            f"✅ Profile extracted: {profile['total_artists']} artists, {len(profile['genres'])} genres"
        )
        print(f"   Sample genres: {profile['genres'][:5]}...")
        print(f"   Sample artists: {profile['artists'][:5]}...")
    except Exception as e:
        print(f"❌ Error extracting Spotify profile: {e}")
        sys.exit(1)
    print(f"   ⏱️ Took {time.time() - t0:.2f} seconds")

    # 2️⃣ Rank genres
    print("\n🎯 Ranking genres...")
    t0 = time.time()
    try:
        raw_genres = profile.get("genres", [])
        keywords = rank_genres(raw_genres, top_n=top_n, expand=True)
        print(f"   ✅ Final search keywords: {keywords}")
    except Exception as e:
        print(f"❌ Error ranking genres: {e}")
        keywords = profile.get("genres", [])[:top_n]
    print(f"   ⏱️ Took {time.time() - t0:.2f} seconds")

    # 3️⃣ Scrape concurrently
    print("\n2️⃣ Scraping events concurrently...")
    t0 = time.time()

    fatsoma_task = scrape_fatsoma_async(keywords=keywords, city=city, max_events_per_keyword=10)
    eventbrite_task = scrape_eventbrite_async(
        city=city, keywords=keywords, max_events_per_keyword=10, max_pages=2
    )

    fatsoma_events, eventbrite_events = await asyncio.gather(fatsoma_task, eventbrite_task)
    print(f"   ⏱️ Took {time.time() - t0:.2f} seconds")

    fatsoma_filtered = [e for e in fatsoma_events if event_matches_city(e, city)]
    eventbrite_filtered = [e for e in eventbrite_events if event_matches_city(e, city)]
    all_events = fatsoma_filtered + eventbrite_filtered

    print(f"\n📊 Total events scraped: {len(all_events)}")
    if not all_events:
        print("❌ No events found from any source.")
        return

    # 4️⃣ Match events
    print("\n3️⃣ Matching events to your music profile...")
    t0 = time.time()
    try:
        matches = match_events_to_profile(all_events, profile)

        if matches:
            print(f"✅ Found {len(matches)} matching events!")
            print("\n🔥 TOP RECOMMENDED EVENTS:")
            print("=" * 50)
            for i, match in enumerate(matches[:10]):
                event = match["event"]
                score = match["score"]
                print(f"\n{i+1}. {event.get('title') or event.get('name', 'Untitled')}")
                print(f"   📅 Date: {event.get('date', 'TBA')}")
                print(f"   📍 Venue: {event.get('venue', 'TBA')}")
                print(f"   🎯 Match Score: {score:.3f}")
                print(f"   🔗 {event.get('url', 'N/A')}")
            print_match_details(matches, limit=3)
        else:
            print("❌ No matching events found.")
    except Exception as e:
        print(f"❌ Error during matching: {e}")
    print(f"   ⏱️ Took {time.time() - t0:.2f} seconds")

    print(f"\n✨ VibeCheck complete! Total runtime: {time.time() - start_total:.2f} seconds")


def main():
    parser = argparse.ArgumentParser(
        description="VibeCheck — match your Spotify playlist to nearby events"
    )
    parser.add_argument(
        "--playlist", "-p", default="400alQ3Ay2Ksb6GKv002Gm", help="Spotify playlist id"
    )
    parser.add_argument("--city", "-c", default="london", help="City to filter events")
    parser.add_argument("--top", "-t", type=int, default=5, help="Top N ranked keywords to use")
    args = parser.parse_args()

    asyncio.run(main_async(args.playlist, args.city, args.top))


if __name__ == "__main__":
    main()
