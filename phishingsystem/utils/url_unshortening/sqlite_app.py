import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DB = os.path.join(BASE_DIR,'url_cache.db')

def init_cache():
    conn = sqlite3.connect(CACHE_DB, timeout=10)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS url_cache (short_url TEXT PRIMARY KEY, expanded_url TEXT)
    """)
    
    conn.commit()
    conn.close()

def get_cached_url(short_url):
    conn = sqlite3.connect(CACHE_DB)
    cur = conn.cursor()
    cur.execute('SELECT expanded_url FROM url_cache WHERE short_url = ?',(short_url,))
    row = cur.fetchone()
    conn.close()

    return row[0] if row else None

def cache_url(short_url,expanded_url):
    conn = sqlite3.connect(CACHE_DB)
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO url_cache (short_url, expanded_url) VALUES (?, ?)',(short_url,expanded_url))
    conn.commit()
    conn.close()