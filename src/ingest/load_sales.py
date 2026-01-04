"""Load and ingest sales data."""

import logging
import pandas as pd
from datetime import datetime, timedelta
from src.utils.db import init_database, get_connection

logger = logging.getLogger(__name__)


def load_sales_data(config: dict) -> pd.DataFrame:
    """
    Load sales data from database.
    
    Returns empty DataFrame with columns: date, item_id, quantity
    if no data exists yet.
    """
    logger.info("Loading sales data...")
    
    # Initialize database if needed
    init_database(config)
    
    # Try to load from database
    conn = get_connection(config)
    
    try:
        df = pd.read_sql_query(
            "SELECT date, item_id, quantity FROM daily_item_sales ORDER BY date, item_id",
            conn
        )
        conn.close()
        
        if df.empty:
            logger.info("No sales data found, returning empty DataFrame")
            return pd.DataFrame(columns=["date", "item_id", "quantity"])
        
        logger.info(f"Loaded {len(df)} sales records")
        return df
        
    except Exception as e:
        logger.warning(f"Error loading sales data: {e}, returning empty DataFrame")
        conn.close()
        return pd.DataFrame(columns=["date", "item_id", "quantity"])


def create_sample_data(config: dict, num_items: int = 3, days: int = 60) -> None:
    """
    Create sample sales data for testing.
    
    Args:
        config: Configuration dictionary
        num_items: Number of sample items to create
        days: Number of days of historical data to generate
    """
    logger.info(f"Creating sample data: {num_items} items, {days} days")
    
    init_database(config)
    conn = get_connection(config)
    cursor = conn.cursor()
    
    # Create sample items
    import random
    for i in range(1, num_items + 1):
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO items (id, name) VALUES (?, ?)",
                (i, f"Item_{i}")
            )
        except Exception as e:
            pass
    
    # Generate sales data
    today = datetime.now()
    sales_records = []
    
    for day_offset in range(days, 0, -1):
        date = today - timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")
        
        for item_id in range(1, num_items + 1):
            # Generate realistic sales with some seasonality
            base_sales = 10 + item_id * 5
            day_of_week = date.weekday()
            # Higher sales on weekends
            weekend_multiplier = 1.5 if day_of_week >= 5 else 1.0
            # Add some randomness
            quantity = max(0, int(base_sales * weekend_multiplier * random.uniform(0.7, 1.3)))
            
            sales_records.append((date_str, item_id, float(quantity)))
    
    # Insert sales data
    cursor.executemany(
        "INSERT OR REPLACE INTO daily_item_sales (date, item_id, quantity) VALUES (?, ?, ?)",
        sales_records
    )
    
    conn.commit()
    conn.close()
    logger.info(f"Created {len(sales_records)} sample sales records")

