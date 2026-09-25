"""Small SQLite store for bot users and bookkeeping (Swati)."""
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  chat_id INTEGER PRIMARY KEY, lang TEXT NOT NULL DEFAULT 'hi', lat REAL, lon REAL,
  node_id TEXT, node_name TEXT, distance_km REAL, phone TEXT,
  subscribed INTEGER NOT NULL DEFAULT 0, updated_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_users_node ON users(node_id, subscribed);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


class Store:
    def __init__(self, path="bot.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def get_user(self, chat_id):
        r = self.conn.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,)).fetchone()
        return None if r is None else dict(r)

    def upsert_user(self, chat_id, **fields):
        now = int(time.time())
        if self.get_user(chat_id) is None:
            self.conn.execute("INSERT INTO users(chat_id, updated_at) VALUES (?,?)", (chat_id, now))
        allowed = {"lang", "lat", "lon", "node_id", "node_name", "distance_km", "phone", "subscribed"}
        for k, v in fields.items():
            if k not in allowed:
                raise ValueError(f"unknown field {k}")
            self.conn.execute(f"UPDATE users SET {k}=?, updated_at=? WHERE chat_id=?", (v, now, chat_id))
        self.conn.commit()
        return self.get_user(chat_id)

    def subscribers_for(self, node_id):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM users WHERE node_id=? AND subscribed=1", (node_id,))]

    def get_meta(self, key, default=None):
        r = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return default if r is None else r["value"]

    def set_meta(self, key, value):
        self.conn.execute("INSERT INTO meta(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                          (key, str(value)))
        self.conn.commit()

    def node_names(self):
        return {r["node_id"]: r["node_name"] for r in self.conn.execute(
            "SELECT DISTINCT node_id, node_name FROM users WHERE node_id IS NOT NULL")}
