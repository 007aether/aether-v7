"""AETHER v7 — Database Layer (unified schema)"""
import sqlite3
from .config import DB_PATH, EARNINGS_DB

SCHEMA_MEMORY = """
CREATE TABLE IF NOT EXISTS cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    observation TEXT,
    decision TEXT,
    action TEXT,
    success INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    level TEXT DEFAULT 'INFO',
    source TEXT,
    message TEXT
);
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,
    value TEXT,
    category TEXT DEFAULT 'general',
    ts TEXT
);
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    description TEXT,
    level INTEGER DEFAULT 1,
    ts TEXT
);
CREATE INDEX IF NOT EXISTS idx_cycles_ts ON cycles(ts);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
"""

SCHEMA_EARNINGS = """
CREATE TABLE IF NOT EXISTS earnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    source TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'confirmed',
    note TEXT
);
CREATE TABLE IF NOT EXISTS depin_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    project TEXT,
    status TEXT,
    daily_usd REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tap_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    bot TEXT,
    status TEXT DEFAULT 'ready',
    last_tap TEXT
);
CREATE TABLE IF NOT EXISTS airdrops_active (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    name TEXT,
    chain TEXT,
    status TEXT DEFAULT 'tracked'
);
CREATE INDEX IF NOT EXISTS idx_earnings_ts ON earnings(ts);
"""

def connect_memory():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.executescript(SCHEMA_MEMORY)
    c.commit()
    return c

def connect_earnings():
    c = sqlite3.connect(EARNINGS_DB, timeout=10)
    c.executescript(SCHEMA_EARNINGS)
    c.commit()
    return c

def init_all():
    connect_memory().close()
    connect_earnings().close()
    print("✓ DBs initialized")
