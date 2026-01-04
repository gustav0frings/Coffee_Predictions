"""Date utility functions."""

from datetime import datetime, timedelta
from typing import List


def get_today() -> str:
    """Get today's date as YYYY-MM-DD string."""
    return datetime.now().strftime("%Y-%m-%d")


def add_days(date_str: str, days: int) -> str:
    """Add days to a date string and return as YYYY-MM-DD."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


def format_date(date_obj: datetime) -> str:
    """Format datetime object as YYYY-MM-DD string."""
    return date_obj.strftime("%Y-%m-%d")


def get_date_range(start_date: str, days: int) -> List[str]:
    """Get a list of date strings from start_date for the specified number of days."""
    dates = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    for _ in range(days):
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates
