"""Generate forecasts using trained model."""

import logging
import joblib
import pandas as pd
from pathlib import Path
from src.utils.db import get_connection
from src.utils.dates import get_today, add_days, get_date_range
from src.features.build_features import build_features

logger = logging.getLogger(__name__)


def generate_forecasts(config: dict) -> pd.DataFrame:
    """
    Generate forecasts for the next forecast horizon days.
    
    Returns:
        DataFrame with columns: date, item_id, predicted_quantity
    """
    logger.info("Generating forecasts...")
    
    # Load latest model
    model_path = Path(config["paths"]["model_dir"]) / "latest.model"
    
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}")
        return pd.DataFrame(columns=["date", "item_id", "predicted_quantity"])
    
    try:
        model = joblib.load(model_path)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return pd.DataFrame(columns=["date", "item_id", "predicted_quantity"])
    
    # Get forecast horizon
    horizon = config["forecast"]["horizon"]
    today = get_today()
    forecast_dates = get_date_range(today, horizon)
    
    # Get all items from database
    conn = get_connection(config)
    try:
        items_df = pd.read_sql_query("SELECT id as item_id FROM items", conn)
        if items_df.empty:
            logger.warning("No items found in database, returning empty forecasts")
            return pd.DataFrame(columns=["date", "item_id", "predicted_quantity"])
    except Exception as e:
        logger.warning(f"Error loading items: {e}, returning empty forecasts")
        conn.close()
        return pd.DataFrame(columns=["date", "item_id", "predicted_quantity"])
    conn.close()
    
    # Build features for forecast period (stub - will be implemented later)
    # For now, create empty feature DataFrame
    forecast_features = pd.DataFrame(columns=[
        "date", "item_id", "lag_1", "lag_7", 
        "rolling_7", "rolling_28", "day_of_week", "month"
    ])
    
    # Generate predictions (stub - will predict zeros for now)
    forecasts = []
    for date in forecast_dates:
        for _, item_row in items_df.iterrows():
            item_id = item_row["item_id"]
            # Placeholder prediction (will use model.predict() when features are ready)
            predicted_quantity = 0.0
            forecasts.append({
                "date": date,
                "item_id": item_id,
                "predicted_quantity": predicted_quantity
            })
    
    forecast_df = pd.DataFrame(forecasts)
    
    # Write to database
    if not forecast_df.empty:
        conn = get_connection(config)
        cursor = conn.cursor()
        
        import uuid
        run_id = str(uuid.uuid4())
        
        for _, row in forecast_df.iterrows():
            cursor.execute(
                """INSERT OR REPLACE INTO forecasts 
                   (date, item_id, predicted_quantity, run_id) 
                   VALUES (?, ?, ?, ?)""",
                (row["date"], row["item_id"], row["predicted_quantity"], run_id)
            )
        
        conn.commit()
        conn.close()
        logger.info(f"Forecasts written to database with run_id: {run_id}")
    
    logger.info(f"Generated {len(forecast_df)} forecasts")
    return forecast_df

