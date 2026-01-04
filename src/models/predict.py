"""Generate forecasts using trained model."""

import logging
from pathlib import Path

import joblib
import pandas as pd

from src.utils.dates import get_date_range, get_today
from src.utils.db import get_connection

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

    # Load historical sales data to build features for forecast period
    from src.ingest.load_sales import load_sales_data

    sales_df = load_sales_data(config)

    # Build features for forecast period
    # We need to create feature rows for each (date, item_id) combination
    forecasts = []
    feature_cols = [
        "lag_1",
        "lag_7",
        "rolling_7",
        "rolling_28",
        "day_of_week",
        "month",
        "promotion_discount",
        "is_holiday",
        "item_id",
    ]

    # Try to load promotion/holiday data for forecast dates from database
    conn = get_connection(config)
    try:
        # Use parameterized query to avoid SQL injection
        placeholders = ",".join(["?" for _ in forecast_dates])
        query = (
            f"SELECT date, item_id, "
            f"COALESCE(promotion_discount, 0) as promotion_discount, "
            f"COALESCE(is_holiday, 0) as is_holiday "
            f"FROM daily_item_sales WHERE date IN ({placeholders})"
        )
        promo_holiday_df = pd.read_sql_query(query, conn, params=forecast_dates)
        promo_holiday_df["promotion_discount"] = (
            promo_holiday_df["promotion_discount"].fillna(0.0).astype(float)
        )
        promo_holiday_df["is_holiday"] = promo_holiday_df["is_holiday"].fillna(0).astype(int)
    except Exception as e:
        logger.warning(f"Could not load promotion/holiday data for forecast dates: {e}")
        promo_holiday_df = pd.DataFrame(
            columns=["date", "item_id", "promotion_discount", "is_holiday"]
        )
    conn.close()

    for date in forecast_dates:
        for _, item_row in items_df.iterrows():
            item_id = item_row["item_id"]

            # Get the most recent sales data for this item to compute features
            item_sales = sales_df[sales_df["item_id"] == item_id].copy()

            if not item_sales.empty:
                item_sales["date"] = pd.to_datetime(item_sales["date"])
                item_sales = item_sales.sort_values("date")

                # Get last known values for lags and rolling averages
                lag_1 = item_sales["quantity"].iloc[-1] if len(item_sales) >= 1 else 0.0
                lag_7 = item_sales["quantity"].iloc[-7] if len(item_sales) >= 7 else 0.0
                rolling_7 = item_sales["quantity"].tail(7).mean() if len(item_sales) >= 1 else 0.0
                rolling_28 = item_sales["quantity"].tail(28).mean() if len(item_sales) >= 1 else 0.0
            else:
                lag_1 = 0.0
                lag_7 = 0.0
                rolling_7 = 0.0
                rolling_28 = 0.0

            # Calendar features for forecast date
            date_obj = pd.to_datetime(date)
            day_of_week = date_obj.dayofweek
            month = date_obj.month

            # Get promotion and holiday data for this date/item combination
            promo_holiday_row = promo_holiday_df[
                (promo_holiday_df["date"] == date) & (promo_holiday_df["item_id"] == item_id)
            ]
            if not promo_holiday_row.empty:
                promotion_discount = float(promo_holiday_row["promotion_discount"].iloc[0])
                is_holiday = int(promo_holiday_row["is_holiday"].iloc[0])
            else:
                # Default to no promotion and not a holiday if data not available
                promotion_discount = 0.0
                is_holiday = 0

            # Build feature vector
            x_features = pd.DataFrame(
                [
                    [
                        lag_1,
                        lag_7,
                        rolling_7,
                        rolling_28,
                        day_of_week,
                        month,
                        promotion_discount,
                        is_holiday,
                        item_id,
                    ]
                ],
                columns=feature_cols,
            )

            # Make prediction
            try:
                predicted_quantity = float(model.predict(x_features)[0])
                # Ensure non-negative
                predicted_quantity = max(0.0, predicted_quantity)
            except Exception as e:
                logger.warning(f"Error predicting for item {item_id} on {date}: {e}")
                predicted_quantity = 0.0

            forecasts.append(
                {"date": date, "item_id": item_id, "predicted_quantity": predicted_quantity}
            )

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
                (row["date"], row["item_id"], row["predicted_quantity"], run_id),
            )

        conn.commit()
        conn.close()
        logger.info(f"Forecasts written to database with run_id: {run_id}")

    logger.info(f"Generated {len(forecast_df)} forecasts")
    return forecast_df
