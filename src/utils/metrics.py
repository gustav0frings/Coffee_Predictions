"""Metrics calculation utilities."""

from typing import Union

import numpy as np
import pandas as pd


def mean_absolute_error(
    y_true: Union[pd.Series, np.ndarray], y_pred: Union[pd.Series, np.ndarray]
) -> float:
    """Calculate Mean Absolute Error (MAE)."""
    if len(y_true) == 0 or len(y_pred) == 0:
        return 0.0

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    return float(np.mean(np.abs(y_true - y_pred)))


def weighted_absolute_percentage_error(
    y_true: Union[pd.Series, np.ndarray], y_pred: Union[pd.Series, np.ndarray]
) -> float:
    """Calculate Weighted Absolute Percentage Error (WAPE)."""
    if len(y_true) == 0 or len(y_pred) == 0:
        return 0.0

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    numerator = np.sum(np.abs(y_true - y_pred))
    denominator = np.sum(np.abs(y_true))

    if denominator == 0:
        return 0.0

    return float(numerator / denominator * 100)
