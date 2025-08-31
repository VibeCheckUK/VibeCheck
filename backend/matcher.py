import re

def match_events_to_profile(events, profile):
    """
    Match events from multiple sources (Fatsoma, Eventbrite) to Spotify profile.
    Uses genres, artists, and keywords to rank events by relevance.
    """
    if not events:
        print("No events to match!")
        return []
    
    # Extract keywords from profile
    keywords = set()
    
    # Add genres (primary matching criteria)
    genres = profile.get("genres", [])
    keywords.update([genre.lower() for genre in genres])
    
    # Add artist names (secondary matching criteria)
    artists = profile.get("artists", [])
    keywords.update([artist.lower() for artist in artists])
    
    # Add some music-related keywords based on genres
    music_keywords = extract_music_keywords(genres)
    keywords.update(music_keywords)
    
    print(f"Matching against {len(keywords)} keywords from profile...")
    print(f"Sample keywords: {list(keywords)[:10]}...")
    
    results = []
    for e in events:
        if not e or not e.get("title"):
            continue
            
        title = e["title"].lower()
        venue = e.get("venue", "").lower() if e.get("venue") else ""
        description = f"{title} {venue}"  # Combine title and venue for matching
        
        score = calculate_event_score(description, keywords, genres, artists)
        
        if score > 0:
            results.append({
                "event": e,
                "score": score,
                "matched_keywords": get_matched_keywords(description, keywords)
            })
    
    # Sort by score (best matches first)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"Found {len(results)} matching events out of {len(events)} total events")
    return results


def calculate_event_score(text, keywords, genres, artists):
    """Calculate relevance score for an event based on text content."""
    score = 0
    text_lower = text.lower()
    
    # Genre matching (highest priority)
    for genre in genres:
        genre_lower = genre.lower()
        if re.search(rf"\b{re.escape(genre_lower)}\b", text_lower):
            score += 5  # Exact genre match gets high score
        elif genre_lower in text_lower:
            score += 3  # Partial genre match
    
    # Artist matching (medium priority)
    for artist in artists:
        artist_lower = artist.lower()
        if re.search(rf"\b{re.escape(artist_lower)}\b", text_lower):
            score += 4  # Exact artist match
        elif artist_lower in text_lower:
            score += 2  # Partial artist match
    
    # General keyword matching (lower priority)
    for keyword in keywords:
        if keyword not in [g.lower() for g in genres] and keyword not in [a.lower() for a in artists]:
            keyword_lower = keyword.lower()
            if re.search(rf"\b{re.escape(keyword_lower)}\b", text_lower):
                score += 2  # Exact keyword match
            elif keyword_lower in text_lower:
                score += 1  # Partial keyword match
    
    # Bonus points for music-related terms
    music_terms = ['concert', 'live', 'music', 'band', 'festival', 'show', 'performance', 'gig']
    for term in music_terms:
        if term in text_lower:
            score += 1
    
    return score


def get_matched_keywords(text, keywords):
    """Get list of keywords that matched in the text."""
    matched = []
    text_lower = text.lower()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if re.search(rf"\b{re.escape(keyword_lower)}\b", text_lower) or keyword_lower in text_lower:
            matched.append(keyword)
    
    return matched[:5]  # Return top 5 matched keywords


def extract_music_keywords(genres):
    """Extract additional music-related keywords based on genres."""
    keywords = set()
    
    # Map genres to related terms
    genre_mappings = {
        'pop': ['pop', 'popular', 'mainstream'],
        'rock': ['rock', 'alternative', 'indie'],
        'hip hop': ['hip hop', 'rap', 'urban', 'hiphop'],
        'electronic': ['electronic', 'edm', 'dance', 'techno', 'house'],
        'jazz': ['jazz', 'blues', 'swing'],
        'classical': ['classical', 'orchestra', 'symphony'],
        'country': ['country', 'folk', 'acoustic'],
        'reggae': ['reggae', 'ska', 'dub'],
        'metal': ['metal', 'heavy', 'hardcore'],
        'punk': ['punk', 'hardcore', 'alternative'],
        'soul': ['soul', 'r&b', 'rnb', 'funk'],
        'world': ['world', 'ethnic', 'traditional'],
        'latin': ['latin', 'salsa', 'bachata', 'reggaeton'],
        'bollywood': ['bollywood', 'indian', 'hindi', 'desi'],
        'tamil': ['tamil', 'kollywood', 'south indian'],
        'telugu': ['telugu', 'tollywood'],
        'malayalam': ['malayalam', 'mollywood'],
        'kannada': ['kannada', 'sandalwood']
    }
    
    for genre in genres:
        genre_lower = genre.lower()
        for key, values in genre_mappings.items():
            if key in genre_lower or any(v in genre_lower for v in values):
                keywords.update(values)
    
    return keywords


def print_match_details(matches, limit=5):
    """Print detailed information about matches for debugging."""
    print(f"\n📊 Match Details (Top {limit}):")
    for i, match in enumerate(matches[:limit]):
        event = match["event"]
        score = match["score"]
        keywords = match.get("matched_keywords", [])
        
        print(f"\n{i+1}. {event['title']}")
        print(f"   Score: {score}")
        print(f"   Venue: {event.get('venue', 'N/A')}")
        print(f"   Date: {event.get('date', 'N/A')}")
        print(f"   Matched Keywords: {', '.join(keywords) if keywords else 'None'}")
        print(f"   URL: {event['url']}")
