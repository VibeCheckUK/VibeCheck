from sentence_transformers import SentenceTransformer, util

# Load a lightweight pre-trained model
model = SentenceTransformer("all-MiniLM-L6-v2")


def match_events_to_profile(events, profile):
    """
    Match events to a Spotify profile using SentenceTransformer embeddings.
    - Removes duplicates BY TITLE
    - Returns all relevant events
    """
    if not events:
        print("No events to match!")
        return []

    genres = [g.lower() for g in profile.get("genres", [])]
    artists = [a.lower() for a in profile.get("artists", [])]

    # Build profile text
    profile_text = " ".join(genres + artists)
    profile_embedding = model.encode(profile_text, convert_to_tensor=True)

    results = []
    # --- THIS IS THE FIX ---
    # We will check for titles we've already seen
    seen_titles = set()
    # -----------------------

    for event in events:
        # --- MODIFIED DEDUPLICATION ---
        # Get the title first for deduplication
        title = event.get("title") or event.get("name") or ""
        if not title:
            continue # Skip events with no title at all

        # Normalize the title to catch duplicates
        normalized_title = title.strip().lower()
        if normalized_title in seen_titles:
            continue  # Skip duplicate title
        seen_titles.add(normalized_title)
        # --- END OF FIX ---

        # Get other fields
        venue = event.get("venue") or ""
        description = event.get("description") or ""
        event_text = f"{title} {venue} {description}".strip().lower()

        # ✅ Optional: genre filter (keep it if you want tighter results)
        if not any(genre in event_text for genre in genres):
            continue

        # ✅ Semantic similarity
        event_embedding = model.encode(event_text, convert_to_tensor=True)
        similarity = float(util.cos_sim(profile_embedding, event_embedding))

        results.append({
            "event": event,
            "score": similarity,
        })

    # Sort by similarity (descending)
    results.sort(key=lambda x: x["score"], reverse=True)

    # Return ALL matching events
    top_results = results
    print(f"Returning {len(top_results)} unique matching events (from {len(events)} total events)")
    return top_results


def print_match_details(matches, limit=5):
    """Print detailed information about matches for debugging."""
    print(f"\n📊 Match Details (Top {limit}):")
    for i, match in enumerate(matches[:limit]):
        event = match["event"]
        score = match["score"]

        print(f"\n{i+1}. {event.get('title', 'Untitled')}")
        print(f"   Score: {score:.3f}")
        print(f"   Venue: {event.get('venue', 'N/A')}")
        print(f"   Date: {event.get('date', 'N/A')}")
        print(f"   URL: {event.get('url', 'N/A')}")