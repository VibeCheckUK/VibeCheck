import requests
import base64
import json
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

def get_access_token():
    """Get Spotify API access token via client credentials flow."""
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,   # space is critical
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = requests.post(url, headers=headers, data=data)
    result.raise_for_status()
    json_result = result.json()

    if "access_token" not in json_result:
        raise Exception(f"Spotify token error: {json_result}")

    return json_result["access_token"]

def get_playlist_tracks(playlist_id, token):
    """Fetch tracks in a Spotify playlist (client credentials safe)."""
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {token}"}
    
    all_tracks = []
    limit = 50  # Max per request
    offset = 0
    
    while True:
        resp = requests.get(url, headers=headers, params={"limit": limit, "offset": offset})
        
        if resp.status_code != 200:
            print("DEBUG STATUS:", resp.status_code)
            print("DEBUG BODY:", resp.text)
            resp.raise_for_status()
        
        data = resp.json()
        items = data.get("items", [])
        all_tracks.extend(items)
        
        # Check if there are more tracks
        if len(items) < limit or not data.get("next"):
            break
            
        offset += limit
    
    return {"items": all_tracks}

def get_artist_genres(artist_ids, token):
    """Get genres for multiple artists (up to 50 at a time)."""
    if not artist_ids:
        return {}
    
    # Spotify allows up to 50 artist IDs per request
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
                if artist:  # Sometimes API returns null for invalid IDs
                    artist_genres[artist["id"]] = artist.get("genres", [])
        else:
            print(f"Warning: Failed to get genres for artist batch: {resp.status_code}")
    
    return artist_genres

def get_audio_features(track_ids, token):
    """Get audio features for multiple tracks (up to 100 at a time)."""
    if not track_ids:
        return {}
    
    audio_features = {}
    
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        ids_string = ",".join(batch)
        
        url = "https://api.spotify.com/v1/audio-features"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"ids": ids_string}
        
        resp = requests.get(url, headers=headers, params=params)
        
        if resp.status_code == 200:
            data = resp.json()
            for features in data.get("audio_features", []):
                if features:  # Sometimes API returns null
                    audio_features[features["id"]] = {
                        "danceability": features.get("danceability", 0),
                        "energy": features.get("energy", 0),
                        "valence": features.get("valence", 0),
                        "acousticness": features.get("acousticness", 0),
                        "instrumentalness": features.get("instrumentalness", 0),
                        "tempo": features.get("tempo", 0)
                    }
        else:
            print(f"Warning: Failed to get audio features for track batch: {resp.status_code}")
    
    return audio_features

def extract_playlist_profile(playlist_id):
    """
    Build a comprehensive 'profile' for the playlist:
    - Unique artist names and IDs
    - Artist genres
    - Track popularity
    """
    token = get_access_token()
    tracks_data = get_playlist_tracks(playlist_id, token)
    
    artists = []
    artist_ids = []
    popularities = []
    
    print(f"Processing {len(tracks_data.get('items', []))} tracks...")
    
    # Extract basic info from tracks
    for item in tracks_data.get("items", []):
        track = item.get("track", {})
        if track and track.get("artists"):
            # Collect artist info
            for artist in track["artists"]:
                if artist["name"] not in artists:
                    artists.append(artist["name"])
                    artist_ids.append(artist["id"])
            
            # Collect track popularity
            if track.get("popularity") is not None:
                popularities.append(track["popularity"])
    
    print(f"Found {len(artists)} unique artists, getting their genres...")
    
    # Get genres for all artists
    artist_genres_dict = get_artist_genres(artist_ids, token)
    all_genres = []
    for genres_list in artist_genres_dict.values():
        all_genres.extend(genres_list)
    
    unique_genres = list(set(all_genres))
    
    print(f"Found {len(unique_genres)} unique genres: {unique_genres[:10]}...")
    
    # Calculate average popularity
    avg_popularity = sum(popularities) / len(popularities) if popularities else 0
    
    profile = {
        "artists": artists,
        "genres": unique_genres,
        "avg_popularity": avg_popularity,
        "total_tracks": len(tracks_data.get("items", [])),
        "total_artists": len(artists)
    }
    
    print(f"Profile complete: {len(artists)} artists, {len(unique_genres)} genres")
    return profile