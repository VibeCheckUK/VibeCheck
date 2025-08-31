import sqlite3
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
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
