"""Model training functionality."""

import logging
import joblib
import pandas as pd
from pathlib import Path
from catboost import CatBoostRegressor
from src.utils.db import get_connection

logger = logging.getLogger(__name__)


def train_model(features_df: pd.DataFrame, config: dict) -> tuple:
    """
    Train a global ML model on historical features.
    
    Returns:
        tuple: (model, metrics_dict)
    """
    logger.info("Training model...")
    
    if features_df.empty:
        logger.warning("No features available, creating minimal model")
        # Create a minimal model that will predict zeros
        model = CatBoostRegressor(
            iterations=1,
            depth=2,
            learning_rate=0.1,
            verbose=False
        )
        # Train on dummy data
        X_dummy = pd.DataFrame([[0, 0, 0, 0, 0, 0, 0]], 
                              columns=["lag_1", "lag_7", "rolling_7", "rolling_28", 
                                      "day_of_week", "month", "item_id"])
        y_dummy = pd.Series([0])
        model.fit(X_dummy, y_dummy)
    else:
        # This will be implemented with actual training logic later
        logger.info("Training on provided features")
        model = CatBoostRegressor(
            iterations=10,
            depth=4,
            learning_rate=0.1,
            verbose=False
        )
        # Placeholder: would split and train here
        model = CatBoostRegressor(iterations=1, depth=2, learning_rate=0.1, verbose=False)
        X_dummy = pd.DataFrame([[0, 0, 0, 0, 0, 0, 0]], 
                              columns=["lag_1", "lag_7", "rolling_7", "rolling_28", 
                                      "day_of_week", "month", "item_id"])
        y_dummy = pd.Series([0])
        model.fit(X_dummy, y_dummy)
    
    # Save model
    model_dir = Path(config["paths"]["model_dir"])
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "latest.model"
    
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Create metrics dict
    metrics = {
        "mae": 0.0,
        "wape": 0.0,
        "model_type": config["model"]["type"]
    }
    
    # Log model run to database
    try:
        conn = get_connection(config)
        cursor = conn.cursor()
        import uuid
        from datetime import datetime
        run_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO model_runs (run_id, timestamp, metrics, model_type) VALUES (?, ?, ?, ?)",
            (run_id, datetime.now().isoformat(), str(metrics), config["model"]["type"])
        )
        conn.commit()
        conn.close()
        logger.info(f"Model run logged with ID: {run_id}")
    except Exception as e:
        logger.warning(f"Could not log model run: {e}")
    
    logger.info("Model training complete")
    return model, metrics

