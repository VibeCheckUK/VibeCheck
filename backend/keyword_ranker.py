# keyword_ranker.py
from collections import Counter
from rapidfuzz import process, fuzz

# Stopwords that shouldn't be used as event keywords
STOPWORDS = {
    "uk", "us", "r", "b", "pop", "music", "rap", "songs", "artist"
}

# Synonym / expansion map for common genres
GENRE_SYNONYMS = {
    "house": ["deep house", "tech house", "progressive house", "slap house"],
    "trance": ["progressive trance", "psytrance", "goa trance"],
    "electro": ["electro house", "electro pop"],
    "drill": ["uk drill", "drill music"],
    "grime": ["uk grime"],
    "afropiano": ["amapiano", "afro piano"],
    "afropop": ["afrobeats", "afro pop"],
    "afro r&b": ["afrobeats r&b", "afro rnb"],
}


def deduplicate_fuzzy(keywords, threshold=85):
    """
    Deduplicate keywords using fuzzy matching.
    Keeps the first occurrence and removes near-duplicates.
    """
    deduped = []
    for kw in keywords:
        if not deduped:
            deduped.append(kw)
            continue
        # Compare against existing keywords
        match, score, _ = process.extractOne(
            kw, deduped, scorer=fuzz.ratio
        )
        if score < threshold:
            deduped.append(kw)
    return deduped


def rank_genres(genres, top_n=5, expand=True):
    """
    Rank genres by frequency and return top N as keywords.
    
    Args:
        genres (list[str]): List of genres from Spotify
        top_n (int): number of keywords to keep
        expand (bool): whether to expand with synonyms
    
    Returns:
        list[str]: Ranked and cleaned keyword list
    """
    if not genres:
        return []

    # Normalize to lowercase
    genres = [g.lower().strip() for g in genres]

    # Count frequency
    counts = Counter(genres)

    # Remove junk/stopwords
    for junk in STOPWORDS:
        counts.pop(junk, None)

    # Get top N
    top_genres = [g for g, _ in counts.most_common(top_n)]

    # Expand with synonyms if enabled
    keywords = []
    for g in top_genres:
        keywords.append(g)
        if expand and g in GENRE_SYNONYMS:
            keywords.extend(GENRE_SYNONYMS[g])

    # Deduplicate with fuzzy matching
    keywords = deduplicate_fuzzy(keywords)

    return keywords


if __name__ == "__main__":
    # Example test
    sample_genres = [
        "progressive house", "trance", "slap house", "electro house", "bass house",
        "uk drill", "grime", "afropiano", "afropop", "afro r&b", "r", "b", "uk"
    ]
    ranked = rank_genres(sample_genres, top_n=6, expand=True)
    print("🎯 Ranked + Expanded (fuzzy deduped):", ranked)
