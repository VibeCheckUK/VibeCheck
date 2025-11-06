import requests
import base64
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# -------------------- ACCESS TOKEN -------------------- #
def get_access_token():
    """Get Spotify API access token using Client Credentials Flow."""
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()
    token_data = resp.json()

    if "access_token" not in token_data:
        raise Exception(f"Spotify token error: {token_data}")

    return token_data["access_token"]


# -------------------- PLAYLIST TRACKS -------------------- #
def get_playlist_tracks(playlist_id, token):
    """Fetch all tracks from a Spotify playlist (handles pagination)."""
    base_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {token}"}

    all_tracks = []
    params = {"limit": 100, "offset": 0}

    while True:
        resp = requests.get(base_url, headers=headers, params=params)

        if resp.status_code == 404:
            raise Exception(
                f"Spotify playlist not found or inaccessible (ID: {playlist_id}). "
                "Make sure it’s a public playlist."
            )

        if resp.status_code != 200:
            raise Exception(f"Spotify API error: {resp.status_code} {resp.text}")

        data = resp.json()
        items = data.get("items", [])
        all_tracks.extend(items)

        if not data.get("next"):
            break

        params["offset"] += params["limit"]

    return {"items": all_tracks}


# -------------------- ARTIST GENRES -------------------- #
def get_artist_genres(artist_ids, token):
    """Retrieve genres for multiple artists in batches of 50."""
    url = "https://api.spotify.com/v1/artists"
    headers = {"Authorization": f"Bearer {token}"}

    artist_genres = {}

    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i + 50]
        resp = requests.get(url, headers=headers, params={"ids": ",".join(batch)})

        if resp.status_code != 200:
            print(f"⚠️ Failed to fetch artist batch {i // 50 + 1}: {resp.text}")
            continue

        data = resp.json()
        for artist in data.get("artists", []):
            if artist:
                artist_genres[artist["id"]] = artist.get("genres", [])

    return artist_genres


# -------------------- PLAYLIST PROFILE -------------------- #
def extract_playlist_profile(playlist_id):
    """
    Build a playlist profile: artists, genres, average popularity, etc.
    Always returns a dict with 'artists' and 'genres'.
    """
    print(f"🎵 Matching from playlist: {playlist_id}")
    token = get_access_token()
    print("✅ Spotify Token Acquired!\n" + "="*50)

    try:
        tracks_data = get_playlist_tracks(playlist_id, token)
    except Exception as e:
        print("❌ SPOTIFY PLAYLIST ERROR")
        print(e)
        print("="*50)
        return {"artists": [], "genres": [], "avg_popularity": 0, "total_tracks": 0, "total_artists": 0}

    artists, artist_ids, popularities = [], [], []
    items = tracks_data.get("items", [])
    print(f"Processing {len(items)} tracks...")

    for item in items:
        track = item.get("track")
        if not track or not track.get("artists"):
            continue

        for artist in track["artists"]:
            if artist["name"] not in artists:
                artists.append(artist["name"])
                artist_ids.append(artist["id"])

        if track.get("popularity") is not None:
            popularities.append(track["popularity"])

    print(f"Found {len(artists)} unique artists, getting genres...")
    artist_genres_dict = get_artist_genres(artist_ids, token)

    all_genres = [genre for genres in artist_genres_dict.values() for genre in genres]
    unique_genres = list(set(all_genres))
    avg_popularity = sum(popularities) / len(popularities) if popularities else 0

    profile = {
        "artists": artists,
        "genres": unique_genres,
        "avg_popularity": avg_popularity,
        "total_tracks": len(items),
        "total_artists": len(artists)
    }

    print(f"✅ Profile complete: {len(artists)} artists, {len(unique_genres)} genres")
    return profile
