import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'data.db'


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_user_id INTEGER UNIQUE NOT NULL,
        tone TEXT NOT NULL DEFAULT 'warm',
        language TEXT NOT NULL DEFAULT 'ru',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_user_id INTEGER NOT NULL,
        thought_text TEXT NOT NULL,
        emotion_label TEXT,
        intensity_before INTEGER,
        distortion TEXT,
        evidence_for TEXT,
        evidence_against TEXT,
        alternative_thought TEXT,
        intensity_after INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Lightweight migrations
    cur.execute("PRAGMA table_info(settings)")
    cols = {r[1] for r in cur.fetchall()}
    if 'reminders_enabled' not in cols:
        cur.execute("ALTER TABLE settings ADD COLUMN reminders_enabled INTEGER NOT NULL DEFAULT 1")

    conn.commit()
    conn.close()
