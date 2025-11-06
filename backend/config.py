import os
from dotenv import load_dotenv

print("DEBUG: Loading .env...")
load_dotenv()
print("DEBUG: .env loaded")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TICKETMASTER_KEY = os.getenv("TICKETMASTER_KEY")
DB_PATH = os.getenv("DB_PATH", "events.db")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")

print("DEBUG SPOTIFY_CLIENT_ID:", SPOTIFY_CLIENT_ID)
print("DEBUG SPOTIFY_CLIENT_SECRET:", SPOTIFY_CLIENT_SECRET)
print("DEBUG EVENTBRITE_TOKEN:", EVENTBRITE_TOKEN)


