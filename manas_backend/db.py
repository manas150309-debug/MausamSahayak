import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
  node_id TEXT PRIMARY KEY, name TEXT, lat REAL NOT NULL, lon REAL NOT NULL,
  district TEXT, state TEXT,
  danger_level_cm REAL,            -- NULL = node has no water-level sensor
  upstream_node_id TEXT,           -- optional: node further up the same river (gives lead time)
  created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS readings (
  id INTEGER PRIMARY KEY AUTOINCREMENT, node_id TEXT NOT NULL, ts INTEGER NOT NULL,
  received_at INTEGER NOT NULL, temperature_c REAL, humidity_pct REAL, pressure_hpa REAL,
  rain_mm REAL, water_level_cm REAL, soil_moisture_pct REAL, battery_v REAL, rssi INTEGER,
  UNIQUE(node_id, ts));
CREATE INDEX IF NOT EXISTS idx_readings_node_ts ON readings(node_id, ts);
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, node_id TEXT NOT NULL, ts INTEGER NOT NULL,
  kind TEXT NOT NULL, level INTEGER NOT NULL, previous_level INTEGER,
  stale INTEGER NOT NULL DEFAULT 0, reasons TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_alerts_node_kind ON alerts(node_id, kind, id);
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  phone TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  alert_location TEXT NOT NULL DEFAULT 'All NCR',
  language TEXT NOT NULL DEFAULT 'en',
  email_alerts INTEGER NOT NULL DEFAULT 1,
  sms_alerts INTEGER NOT NULL DEFAULT 1,
  active INTEGER NOT NULL DEFAULT 1,
  created_at INTEGER NOT NULL,
  last_login_at INTEGER);
CREATE TABLE IF NOT EXISTS notification_deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  alert_id INTEGER,
  channel TEXT NOT NULL,
  destination_masked TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  created_at INTEGER NOT NULL,
  UNIQUE(user_id, alert_id, channel));
CREATE INDEX IF NOT EXISTS idx_notification_user ON notification_deliveries(user_id, id);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(nodes)")}
    if "upstream_node_id" not in cols:            # migrate databases created before this column existed
        conn.execute("ALTER TABLE nodes ADD COLUMN upstream_node_id TEXT")
    conn.commit()
