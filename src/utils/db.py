"""Database utilities for SQLite operations."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_db_path(config: dict) -> Path:
    """Get database path from config."""
    db_path = Path(config["database"]["path"])
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_database(config: dict) -> None:
    """Initialize database and create all required tables."""
    db_path = get_db_path(config)
    
    logger.info(f"Initializing database at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create daily_item_sales table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_item_sales (
            date TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            PRIMARY KEY (date, item_id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Create forecasts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            date TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            predicted_quantity REAL NOT NULL,
            run_id TEXT NOT NULL,
            PRIMARY KEY (date, item_id, run_id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Create model_runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            metrics TEXT,
            model_type TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    logger.info("Database initialized successfully")


def get_connection(config: dict) -> sqlite3.Connection:
    """Get a connection to the database."""
    db_path = get_db_path(config)
    return sqlite3.connect(str(db_path))

