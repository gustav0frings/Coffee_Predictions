"""Build time-series features from sales data."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def build_features(sales_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Build time-series features from sales data.

    Returns DataFrame with feature columns:
    - date, item_id (identifiers)
    - lag_1, lag_7 (lagged sales)
    - rolling_7, rolling_28 (rolling averages)
    - day_of_week, month (calendar features)
    - promotion_discount, is_holiday (promotion and holiday features)
    - quantity (target variable)
    """
    logger.info("Building features...")

    if sales_df.empty:
        logger.info("No sales data, returning empty feature DataFrame")
        return pd.DataFrame(
            columns=[
                "date",
                "item_id",
                "lag_1",
                "lag_7",
                "rolling_7",
                "rolling_28",
                "day_of_week",
                "month",
                "promotion_discount",
                "is_holiday",
                "quantity",
            ]
        )

    # Ensure date is datetime
    sales_df = sales_df.copy()
    sales_df["date"] = pd.to_datetime(sales_df["date"])

    # Sort by date and item_id
    sales_df = sales_df.sort_values(["item_id", "date"])

    # Initialize feature DataFrame with all available columns
    base_cols = ["date", "item_id", "quantity"]
    if "promotion_discount" in sales_df.columns:
        base_cols.append("promotion_discount")
    if "is_holiday" in sales_df.columns:
        base_cols.append("is_holiday")

    feature_df = sales_df[base_cols].copy()

    # Ensure promotion_discount and is_holiday exist with defaults
    if "promotion_discount" not in feature_df.columns:
        feature_df["promotion_discount"] = 0.0
    else:
        feature_df["promotion_discount"] = (
            feature_df["promotion_discount"].fillna(0.0).astype(float)
        )

    if "is_holiday" not in feature_df.columns:
        feature_df["is_holiday"] = 0
    else:
        feature_df["is_holiday"] = feature_df["is_holiday"].fillna(0).astype(int)

    # Calendar features
    feature_df["day_of_week"] = feature_df["date"].dt.dayofweek
    feature_df["month"] = feature_df["date"].dt.month

    # Lag features (grouped by item_id)
    feature_df["lag_1"] = feature_df.groupby("item_id")["quantity"].shift(1).fillna(0)
    feature_df["lag_7"] = feature_df.groupby("item_id")["quantity"].shift(7).fillna(0)

    # Rolling averages (grouped by item_id)
    feature_df["rolling_7"] = (
        feature_df.groupby("item_id")["quantity"]
        .transform(lambda x: x.rolling(window=7, min_periods=1).mean())
        .fillna(0)
    )
    feature_df["rolling_28"] = (
        feature_df.groupby("item_id")["quantity"]
        .transform(lambda x: x.rolling(window=28, min_periods=1).mean())
        .fillna(0)
    )

    # Convert date back to string for consistency
    feature_df["date"] = feature_df["date"].dt.strftime("%Y-%m-%d")

    logger.info(f"Feature building complete: {len(feature_df)} rows with features")
    return feature_df
