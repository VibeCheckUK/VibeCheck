from sentence_transformers import SentenceTransformer, util

# --- THIS IS THE FIX ---
# 1. Don't load the model here. Set it to None.
model = None
# -----------------------

def match_events_to_profile(events, profile):
    """
    Match events to a Spotify profile using SentenceTransformer embeddings.
    - Removes duplicates BY TITLE
    - Returns all relevant events
    """
    
    # --- THIS IS THE FIX ---
    # 2. "Lazy load" the model.
    # Check if the model has been loaded yet.
    global model
    if model is None:
        print("Loading SentenceTransformer model for the first time...")
        # If not, load it now. This will only happen on the first request.
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded successfully.")
    # --- END OF FIX ---

    if not events:
        print("No events to match!")
        return []

    genres = [g.lower() for g in profile.get("genres", [])]
    artists = [a.lower() for a in profile.get("artists", [])]

    # Build profile text
    profile_text = " ".join(genres + artists)
    profile_embedding = model.encode(profile_text, convert_to_tensor=True)

    results = []
    seen_titles = set()

    for event in events:
        title = event.get("title") or event.get("name") or ""
        if not title:
            continue

        normalized_title = title.strip().lower()
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)

        venue = event.get("venue") or ""
        description = event.get("description") or ""
        event_text = f"{title} {venue} {description}".strip().lower()

        if not any(genre in event_text for genre in genres):
            continue

        event_embedding = model.encode(event_text, convert_to_tensor=True)
        similarity = float(util.cos_sim(profile_embedding, event_embedding))

        results.append({
            "event": event,
            "score": similarity,
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    top_results = results
    print(f"Returning {len(top_results)} unique matching events (from {len(events)} total events)")
    return top_results


def print_match_details(matches, limit=5):
    """Print detailed information about matches for debugging."""
    print(f"\n📊 Match Details (Top {limit}):")
    # (Rest of this function is unchanged)
    for i, match in enumerate(matches[:limit]):
        event = match["event"]
        score = match["score"]

        print(f"\n{i+1}. {event.get('title', 'Untitled')}")
        print(f"   Score: {score:.3f}")
        print(f"   Venue: {event.get('venue', 'N/A')}")
        print(f"   Date: {event.get('date', 'N/A')}")
        print(f"   URL: {event.get('url', 'N/A')}")