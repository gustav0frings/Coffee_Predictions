"""Load and ingest sales data."""

import logging
import pandas as pd
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

