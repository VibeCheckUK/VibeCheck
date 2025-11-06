# backend_app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio

# Your original imports
from run import main_async
from recommend_from_playlist import recommend_events_from_playlist
from spotify_client import extract_playlist_profile
from fatsoma_client import scrape_fatsoma_async
from eventbrite_client import scrape_eventbrite_async
from matcher import match_events_to_profile
from keyword_ranker import rank_genres

app = Flask(__name__)
CORS(app)  # Allows your frontend to connect

# Home route
@app.route("/")
def home():
    return "✅ VibeCheck backend API is running!"

@app.route("/api/match", methods=["POST"])
def match_endpoint():
    data = request.get_json()
    
    # Get data from the POST request
    playlist_id = data.get("playlist_id")
    keywords_from_form = data.get("keywords")
    city = data.get("city", "london")
    top_n = data.get("top_n", 5)
    
    budget = data.get("budget", "any") # Get 'budget', default to 'any'
    when = data.get("when", "any")     # Get 'when', default to 'any'

    # Run async logic
    async def run_matching():
        
        if playlist_id:
            # Logic for Spotify Form
            print(f"🎵 Matching from playlist: {playlist_id}")
            profile = extract_playlist_profile(playlist_id)
            raw_genres = profile.get("genres", [])
            keywords = rank_genres(raw_genres, top_n=top_n) 
        elif keywords_from_form:
            # Logic for Preferences Form
            print(f"🎵 Matching from keywords: {keywords_from_form}")
            profile = {"genres": keywords_from_form, "artists": keywords_from_form}
            keywords = keywords_from_form[:top_n]
        else:
            return []

        if not keywords:
             print("❌ No keywords found after ranking.")
             return []

        print(f"🔑 Using ranked keywords: {keywords}")
        print(f"📅 Filtering for 'when': {when}")
        print(f"💰 Filtering for 'budget': {budget}")
        
        # --- THIS IS THE FIX ---
        
        # Eventbrite task always runs, as its filters are reliable
        eventbrite_task = scrape_eventbrite_async(
            city=city, keywords=keywords, max_events_per_keyword=10, max_pages=2,
            budget=budget, when=when
        )

        # If the user wants "Free" events, we ONLY search Eventbrite
        # to guarantee accuracy.
        if budget == "free":
            print("💰 'Free' filter selected. Skipping Fatsoma to ensure 100% accuracy.")
            
            # Run Eventbrite and a dummy task for Fatsoma
            fatsoma_events, eventbrite_events = await asyncio.gather(
                asyncio.sleep(0, []), # A no-op task that returns an empty list
                eventbrite_task
            )
            fatsoma_events = [] # Ensure it's an empty list
        
        else:
            # If any other budget is selected, search both
            print("💰 Budget is not 'Free'. Searching Fatsoma (filter may be inaccurate).")
            fatsoma_task = scrape_fatsoma_async(
                keywords=keywords, city=city, max_events_per_keyword=10, 
                budget=budget, when=when
            )
            fatsoma_events, eventbrite_events = await asyncio.gather(
                fatsoma_task,
                eventbrite_task
            )
        # --- END OF FIX ---
            
        
        print(f"📊 Scraped {len(fatsoma_events or [])} Fatsoma and {len(eventbrite_events or [])} Eventbrite events")

        all_events = (fatsoma_events or []) + (eventbrite_events or [])
        if not all_events:
            return []
            
        matches = match_events_to_profile(all_events, profile)
        
        flat_matches = [match["event"] for match in matches]
        print(f"✅ Found {len(flat_matches)} unique matching events.")
        return flat_matches

    # Run the async function and get results
    events = asyncio.run(run_matching())
    return jsonify({"events": events})

# This line lets you run "python backend_app.py"
if __name__ == "__main__":
    app.run(debug=True, port=5000)