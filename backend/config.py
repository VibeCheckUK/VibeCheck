import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TICKETMASTER_KEY = os.getenv("TICKETMASTER_KEY")
DB_PATH = os.getenv("DB_PATH", "events.db")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
print("DEBUG EVENTBRITE_TOKEN:", EVENTBRITE_TOKEN)

