import requests
import base64
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

def get_access_token():
    """Get Spotify API access token via client credentials flow."""
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()
    json_resp = resp.json()
    if "access_token" not in json_resp:
        raise Exception(f"Spotify token error: {json_resp}")
    return json_resp["access_token"]

def get_playlist_tracks(playlist_id, token):
    """Fetch tracks in a Spotify playlist."""
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {token}"}
    all_tracks = []
    limit = 50
    offset = 0

    while True:
        resp = requests.get(url, headers=headers, params={"limit": limit, "offset": offset})
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        all_tracks.extend(items)
        if len(items) < limit or not data.get("next"):
            break
        offset += limit

    return {"items": all_tracks}

def get_artist_genres(artist_ids, token):
    """Get genres for multiple artists."""
    artist_genres = {}
    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i+50]
        ids_string = ",".join(batch)
        url = "https://api.spotify.com/v1/artists"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"ids": ids_string}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            for artist in data.get("artists", []):
                if artist:
                    artist_genres[artist["id"]] = artist.get("genres", [])
    return artist_genres

def extract_playlist_profile(playlist_id):
    """
    Build a comprehensive profile for the playlist.
    Always returns a dict with 'artists' and 'genres'.
    """
    token = get_access_token()
    tracks_data = get_playlist_tracks(playlist_id, token)
    
    artists, artist_ids, popularities = [], [], []

    print(f"Processing {len(tracks_data.get('items', []))} tracks...")
    for item in tracks_data.get("items", []):
        track = item.get("track", {})
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
        "artists": artists or [],
        "genres": unique_genres or [],
        "avg_popularity": avg_popularity,
        "total_tracks": len(tracks_data.get("items", [])),
        "total_artists": len(artists)
    }

    print(f"Profile complete: {len(artists)} artists, {len(unique_genres)} genres")
    return profile
