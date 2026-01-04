"""Utility script to view database contents."""

import argparse
import sqlite3
import pandas as pd
from pathlib import Path
import yaml


def view_items(config: dict):
    """View all items in the database."""
    conn = sqlite3.connect(config["database"]["path"])
    df = pd.read_sql_query("SELECT * FROM items ORDER BY id", conn)
    conn.close()
    
    if df.empty:
        print("No items found in database.")
    else:
        print(f"\n=== ITEMS ({len(df)} total) ===")
        print(df.to_string(index=False))
    return df


def view_sales(config: dict, limit: int = 20, item_id: int = None):
    """View sales data."""
    conn = sqlite3.connect(config["database"]["path"])
    
    query = "SELECT date, item_id, quantity FROM daily_item_sales"
    if item_id:
        query += f" WHERE item_id = {item_id}"
    query += " ORDER BY date DESC, item_id LIMIT ?"
    
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    
    if df.empty:
        print("No sales data found in database.")
    else:
        print(f"\n=== SALES DATA (showing {len(df)} most recent) ===")
        print(df.to_string(index=False))
        if len(df) > 0:
            print(f"\nSummary: {len(df)} records, avg quantity: {df['quantity'].mean():.2f}")
    return df


def view_forecasts(config: dict, limit: int = 21, latest_only: bool = True):
    """View forecasts."""
    conn = sqlite3.connect(config["database"]["path"])
    
    if latest_only:
        # Get only the latest run
        query = """
            SELECT date, item_id, predicted_quantity, run_id
            FROM forecasts 
            WHERE run_id = (SELECT run_id FROM forecasts ORDER BY run_id DESC LIMIT 1)
            ORDER BY date, item_id
            LIMIT ?
        """
    else:
        query = """
            SELECT date, item_id, predicted_quantity, run_id
            FROM forecasts 
            ORDER BY run_id DESC, date, item_id
            LIMIT ?
        """
    
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    
    if df.empty:
        print("No forecasts found in database.")
    else:
        print(f"\n=== FORECASTS (showing {len(df)} records) ===")
        print(df.to_string(index=False))
        if len(df) > 0:
            print(f"\nSummary:")
            print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
            print(f"  Average prediction: {df['predicted_quantity'].mean():.2f}")
            print(f"  Range: {df['predicted_quantity'].min():.2f} - {df['predicted_quantity'].max():.2f}")
    return df


def view_model_runs(config: dict):
    """View model training runs."""
    conn = sqlite3.connect(config["database"]["path"])
    df = pd.read_sql_query(
        "SELECT run_id, timestamp, model_type, metrics FROM model_runs ORDER BY timestamp DESC LIMIT 10",
        conn
    )
    conn.close()
    
    if df.empty:
        print("No model runs found in database.")
    else:
        print(f"\n=== MODEL RUNS (showing {len(df)} most recent) ===")
        print(df.to_string(index=False))
    return df


def main():
    parser = argparse.ArgumentParser(description="View database contents")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")
    parser.add_argument("--items", action="store_true", help="View items")
    parser.add_argument("--sales", action="store_true", help="View sales data")
    parser.add_argument("--forecasts", action="store_true", help="View forecasts")
    parser.add_argument("--runs", action="store_true", help="View model runs")
    parser.add_argument("--all", action="store_true", help="View all data")
    parser.add_argument("--limit", type=int, default=20, help="Limit number of records")
    parser.add_argument("--item-id", type=int, help="Filter by item ID")
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # View requested data
    if args.all or args.items:
        view_items(config)
    
    if args.all or args.sales:
        view_sales(config, limit=args.limit, item_id=args.item_id)
    
    if args.all or args.forecasts:
        view_forecasts(config, limit=args.limit)
    
    if args.all or args.runs:
        view_model_runs(config)
    
    # If nothing specified, show summary
    if not any([args.items, args.sales, args.forecasts, args.runs, args.all]):
        print("=== DATABASE SUMMARY ===")
        view_items(config)
        view_sales(config, limit=5)
        view_forecasts(config, limit=7)
        print("\nUse --all to see all data, or --items, --sales, --forecasts, --runs for specific views")


if __name__ == "__main__":
    main()

