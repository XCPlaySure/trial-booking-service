import sqlite3
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def connect(db_path=":memory:"):
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
