# db.py
import sqlite3
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the database if it doesn't exist."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            name TEXT,
            url TEXT,
            date TEXT,
            genre TEXT,
            subgenre TEXT,
            venue_city TEXT
        )
    """)
    conn.commit()
    conn.close()

def store_event(event):
    """Insert or replace a single event dictionary into the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO events (id, name, url, date, genre, subgenre, venue_city)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event.get("id"),
        event.get("name"),
        event.get("url"),
        event.get("date"),
        event.get("genre"),
        event.get("subgenre"),
        event.get("venue_city"),
    ))
    conn.commit()
    conn.close()
