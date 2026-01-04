"""Build time-series features from sales data."""

import logging
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


def build_features(sales_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Build time-series features from sales data.
    
    Returns DataFrame with feature columns:
    - date, item_id (identifiers)
    - lag_1, lag_7 (lagged sales)
    - rolling_7, rolling_28 (rolling averages)
    - day_of_week, month (calendar features)
    """
    logger.info("Building features...")
    
    if sales_df.empty:
        logger.info("No sales data, returning empty feature DataFrame")
        return pd.DataFrame(columns=[
            "date", "item_id", "lag_1", "lag_7", 
            "rolling_7", "rolling_28", "day_of_week", "month"
        ])
    
    # For now, return empty features DataFrame with proper structure
    # This will be implemented with actual feature engineering later
    feature_df = pd.DataFrame(columns=[
        "date", "item_id", "lag_1", "lag_7", 
        "rolling_7", "rolling_28", "day_of_week", "month"
    ])
    
    logger.info("Feature building complete (stub implementation)")
    return feature_df

