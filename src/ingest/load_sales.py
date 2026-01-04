"""Load and ingest sales data."""

import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import re
from src.utils.db import init_database, get_connection

logger = logging.getLogger(__name__)


def clean_spanish_number(value):
    """
    Convert Spanish-formatted number to float.
    Handles formats like: "1.234,56" -> 1234.56, "1,234.56" -> 1234.56
    """
    if pd.isna(value) or value == '' or value == 0:
        return 0.0
    
    # Convert to string and remove quotes
    str_val = str(value).strip().replace('"', '').replace("'", "")
    
    # If it's already a simple number, return it
    try:
        return float(str_val)
    except ValueError:
        pass
    
    # Handle Spanish format: thousands with dots, decimals with commas
    # e.g., "1.234,56" -> 1234.56
    if ',' in str_val and '.' in str_val:
        # Check if comma is decimal separator (more digits after comma)
        parts = str_val.replace('.', '').split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Spanish format: dots are thousands, comma is decimal
            return float(parts[0] + '.' + parts[1])
        else:
            # US format: comma is thousands, dot is decimal
            return float(str_val.replace(',', ''))
    elif ',' in str_val:
        # Could be decimal separator or thousands
        if str_val.count(',') == 1 and len(str_val.split(',')[1]) <= 2:
            # Likely decimal separator
            return float(str_val.replace(',', '.'))
        else:
            # Likely thousands separator
            return float(str_val.replace(',', ''))
    elif '.' in str_val:
        # Could be decimal or thousands separator
        parts = str_val.split('.')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely decimal separator
            return float(str_val)
        else:
            # Likely thousands separator
            return float(str_val.replace('.', ''))
    
    # Last resort: try to parse as-is
    try:
        return float(str_val)
    except ValueError:
        return 0.0


def preprocess_hipos_file(hipos_file_path: str, date: str = None, config: dict = None) -> None:
    """
    Preprocess HIPOS output CSV file and load into database.
    
    Args:
        hipos_file_path: Path to HIPOS output CSV file
        date: Date for the sales data in YYYY-MM-DD format. If None, uses today's date.
        config: Configuration dictionary (required for database operations)
    
    The HIPOS file is expected to have:
    - Column 0: Referencia (item reference code)
    - Column 1: Artículo (item name)
    - Column 7: Venta (sales quantity, negative values indicate sales)
    - Other columns: Stock, costs, etc. (not used)
    """
    if config is None:
        raise ValueError("config parameter is required")
    
    logger.info(f"Preprocessing HIPOS file: {hipos_file_path}")
    
    # Determine date
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"No date provided, using today's date: {date}")
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
    
    # Read HIPOS file
    file_path = Path(hipos_file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"HIPOS file not found: {hipos_file_path}")
    
    # Read CSV with proper encoding (try UTF-8 first, then latin-1)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        logger.warning("UTF-8 encoding failed, trying latin-1")
        df = pd.read_csv(file_path, encoding='latin-1')
    
    logger.info(f"Loaded {len(df)} rows from HIPOS file")
    
    # Initialize database
    init_database(config)
    conn = get_connection(config)
    cursor = conn.cursor()
    
    # Process each row
    sales_records = []
    items_created = set()
    
    for idx, row in df.iterrows():
        try:
            # Extract item reference (column 0)
            referencia = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
            if not referencia or referencia == 'nan':
                continue
            
            # Extract item name (column 1) for creating items
            articulo = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else referencia
            
            # Extract sales quantity (column 8, index 8 = "Venta")
            venta_raw = row.iloc[8] if len(row) > 8 else 0
            
            # Clean and convert sales quantity
            venta_quantity = clean_spanish_number(venta_raw)
            
            # Sales are negative in HIPOS, convert to positive quantity
            quantity = abs(venta_quantity) if venta_quantity < 0 else 0.0
            
            # Skip if no sales
            if quantity == 0:
                continue
            
            # Get or create item
            item_id = None
            item_was_created = False
            
            # First, try to find item by name containing referencia
            cursor.execute("SELECT id FROM items WHERE name LIKE ?", (f"%{referencia}%",))
            item_result = cursor.fetchone()
            
            if item_result:
                item_id = item_result[0]
            else:
                # Try to use referencia as ID if it's numeric
                try:
                    potential_id = int(referencia)
                    # Check if this ID already exists
                    cursor.execute("SELECT id FROM items WHERE id = ?", (potential_id,))
                    if cursor.fetchone():
                        item_id = potential_id
                    else:
                        # ID doesn't exist, use it for new item
                        item_id = potential_id
                        item_was_created = True
                except (ValueError, TypeError):
                    # Referencia is not numeric, get next available ID
                    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM items")
                    item_id = cursor.fetchone()[0]
                    item_was_created = True
                
                # Insert new item (only if it doesn't exist)
                cursor.execute(
                    "INSERT OR IGNORE INTO items (id, name) VALUES (?, ?)",
                    (item_id, f"{articulo} ({referencia})")
                )
                # Check if row was actually inserted
                if item_was_created:
                    # Verify it was created (not ignored)
                    cursor.execute("SELECT id FROM items WHERE id = ? AND name = ?", 
                                 (item_id, f"{articulo} ({referencia})"))
                    if cursor.fetchone():
                        items_created.add(item_id)
            
            # Add to sales records
            sales_records.append((date, item_id, float(quantity), 0.0, 0))
            
        except Exception as e:
            logger.warning(f"Error processing row {idx}: {e}")
            continue
    
    # Aggregate sales by item_id (in case same item appears multiple times)
    sales_dict = {}
    for date_str, item_id, qty, promo, holiday in sales_records:
        key = (date_str, item_id)
        if key in sales_dict:
            sales_dict[key] = (date_str, item_id, sales_dict[key][2] + qty, promo, holiday)
        else:
            sales_dict[key] = (date_str, item_id, qty, promo, holiday)
    
    # Insert aggregated sales data
    aggregated_records = list(sales_dict.values())
    cursor.executemany(
        "INSERT OR REPLACE INTO daily_item_sales (date, item_id, quantity, promotion_discount, is_holiday) VALUES (?, ?, ?, ?, ?)",
        aggregated_records
    )
    
    conn.commit()
    conn.close()
    
    logger.info(f"Preprocessed HIPOS file: created {len(items_created)} new items, inserted {len(aggregated_records)} sales records for date {date}")


def load_sales_data(config: dict) -> pd.DataFrame:
    """
    Load sales data from database.
    
    Returns empty DataFrame with columns: date, item_id, quantity, promotion_discount, is_holiday
    if no data exists yet.
    """
    logger.info("Loading sales data...")
    
    # Initialize database if needed
    init_database(config)
    
    # Try to load from database
    conn = get_connection(config)
    
    try:
        df = pd.read_sql_query(
            "SELECT date, item_id, quantity, COALESCE(promotion_discount, 0) as promotion_discount, COALESCE(is_holiday, 0) as is_holiday FROM daily_item_sales ORDER BY date, item_id",
            conn
        )
        conn.close()
        
        if df.empty:
            logger.info("No sales data found, returning empty DataFrame")
            return pd.DataFrame(columns=["date", "item_id", "quantity", "promotion_discount", "is_holiday"])
        
        # Ensure proper types
        df["promotion_discount"] = df["promotion_discount"].fillna(0.0).astype(float)
        df["is_holiday"] = df["is_holiday"].fillna(0).astype(int)
        
        logger.info(f"Loaded {len(df)} sales records")
        return df
        
    except Exception as e:
        logger.warning(f"Error loading sales data: {e}, returning empty DataFrame")
        conn.close()
        return pd.DataFrame(columns=["date", "item_id", "quantity", "promotion_discount", "is_holiday"])


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
        day_of_week = date.weekday()
        
        # Determine if this is a holiday (~10% of days, with some preference for weekends and month-end)
        is_holiday = 0
        if random.random() < 0.1 or (day_of_week >= 5 and random.random() < 0.2) or (date.day >= 28 and random.random() < 0.15):
            is_holiday = 1
        
        for item_id in range(1, num_items + 1):
            # Generate promotion discount (~15% of days have promotions)
            promotion_discount = 0.0
            if random.random() < 0.15:
                promotion_discount = round(random.uniform(10.0, 30.0), 1)
            
            # Generate realistic sales with some seasonality
            base_sales = 10 + item_id * 5
            # Higher sales on weekends
            weekend_multiplier = 1.5 if day_of_week >= 5 else 1.0
            # Promotions boost sales (1.2x to 1.5x multiplier based on discount)
            promotion_multiplier = 1.0 + (promotion_discount / 100.0) * 0.5 if promotion_discount > 0 else 1.0
            # Holidays may affect sales (slight increase)
            holiday_multiplier = 1.1 if is_holiday else 1.0
            # Add some randomness
            quantity = max(0, int(base_sales * weekend_multiplier * promotion_multiplier * holiday_multiplier * random.uniform(0.7, 1.3)))
            
            sales_records.append((date_str, item_id, float(quantity), float(promotion_discount), int(is_holiday)))
    
    # Insert sales data
    cursor.executemany(
        "INSERT OR REPLACE INTO daily_item_sales (date, item_id, quantity, promotion_discount, is_holiday) VALUES (?, ?, ?, ?, ?)",
        sales_records
    )
    
    conn.commit()
    conn.close()
    logger.info(f"Created {len(sales_records)} sample sales records")

