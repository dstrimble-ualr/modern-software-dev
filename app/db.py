"""Database access using SQLite from the standard library.

The real app uses a file on disk (APP_DB_PATH, default app.db).
Tests use ":memory:" so each test run starts from a fresh, seeded database
and nothing is written to disk. Same SQL either way.
"""
import sqlite3

SEED_WIDGETS = [
    ("Widget A", "A basic widget", 9.99),
    ("Widget B", "An advanced widget", 19.99),
    ("Widget C", "A premium widget", 29.99),
]


def connect(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn, admin_password="password"):
    """Create tables and seed a default user and widgets if they do not exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS widgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            price REAL NOT NULL DEFAULT 0
        );
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        ("admin", admin_password),
    )
    conn.executemany(
        "INSERT OR IGNORE INTO widgets (name, description, price) VALUES (?, ?, ?)",
        SEED_WIDGETS,
    )
    conn.commit()


def find_user(conn, username, password):
    row = conn.execute(
        "SELECT id, username FROM users WHERE username = ? AND password = ?",
        (username, password),
    ).fetchone()
    return dict(row) if row else None


def list_widgets(conn):
    rows = conn.execute(
        "SELECT id, name, description, price FROM widgets ORDER BY id"
    ).fetchall()
    return [dict(row) for row in rows]
