"""Main pipeline orchestrator."""

import argparse
import logging
import sys
from pathlib import Path
import yaml

from src.utils.db import init_database
from src.ingest.load_sales import load_sales_data
from src.features.build_features import build_features
from src.models.train import train_model
from src.models.predict import generate_forecasts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Sales Forecasting Pipeline")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["predict", "retrain"],
        default="predict",
        help="Pipeline mode: 'predict' (forecast only) or 'retrain' (retrain + forecast)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to config file"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    config = load_config(config_path)
    
    # Initialize database
    logger.info("Initializing database...")
    init_database(config)
    
    try:
        # Step 1: Load sales data
        logger.info("=" * 50)
        logger.info("Step 1: Loading sales data")
        logger.info("=" * 50)
        sales_df = load_sales_data(config)
        
        # Step 2: Build features
        logger.info("=" * 50)
        logger.info("Step 2: Building features")
        logger.info("=" * 50)
        features_df = build_features(sales_df, config)
        
        # Step 3: Train model (if retrain mode)
        if args.mode == "retrain":
            logger.info("=" * 50)
            logger.info("Step 3: Training model")
            logger.info("=" * 50)
            model, metrics = train_model(features_df, config)
            logger.info(f"Training metrics: {metrics}")
        
        # Step 4: Generate forecasts
        logger.info("=" * 50)
        logger.info("Step 4: Generating forecasts")
        logger.info("=" * 50)
        forecasts_df = generate_forecasts(config)
        
        logger.info("=" * 50)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 50)
        logger.info(f"Generated {len(forecasts_df)} forecasts")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

