# Sample Data

This folder contains example input and output data to help you understand the data format expected by the sales forecasting pipeline.

## Files

### `sample_items.csv`
Master data for items in the system.

**Columns:**
- `id`: Unique item identifier (integer)
- `name`: Item name (string)
- `created_at`: Timestamp when item was created

**Example:**
```csv
id,name,created_at
1,Item_1,2026-01-04 22:37:48
2,Item_2,2026-01-04 22:37:48
3,Item_3,2026-01-04 22:37:48
```

---

### `sample_sales_input.csv`
Historical daily sales data - this is the **input** data used for training and feature building.

**Columns:**
- `date`: Date in YYYY-MM-DD format
- `item_id`: Foreign key to items table
- `quantity`: Number of units sold (float)

**Format:**
- One row per item per day
- Dates should be consecutive (no gaps required, but recommended)
- Quantity should be non-negative

**Example:**
```csv
date,item_id,quantity
2025-11-05,1,18.0
2025-11-05,2,21.0
2025-11-05,3,25.0
2025-11-06,1,13.0
```

**Note:** This file shows 30 days of sample data (90 rows = 30 days × 3 items).

---

### `sample_forecasts_output.csv`
Generated forecasts - this is the **output** from the prediction pipeline.

**Columns:**
- `date`: Forecast date in YYYY-MM-DD format
- `item_id`: Item identifier
- `predicted_quantity`: Forecasted number of units (float)
- `run_id`: Unique identifier for this forecast run (allows tracking multiple forecast runs)

**Format:**
- One row per item per forecast date
- Forecast horizon: 7 days (configurable in `config/config.yaml`)
- Predictions are non-negative floats

**Example:**
```csv
date,item_id,predicted_quantity,run_id
2026-01-04,1,23.44,f2895abd-39ba-4640-8d0c-f55a74ef48f3
2026-01-04,2,24.51,f2895abd-39ba-4640-8d0c-f55a74ef48f3
2026-01-04,3,30.00,f2895abd-39ba-4640-8d0c-f55a74ef48f3
```

**Note:** This file shows forecasts for the next 7 days (21 rows = 7 days × 3 items).

---

### `sample_model_run.csv`
Metadata about model training runs.

**Columns:**
- `run_id`: Unique identifier for this training run
- `timestamp`: When the model was trained (ISO format)
- `model_type`: Type of model used (catboost, lightgbm, or fallback)
- `metrics`: Training metrics as string (MAE, WAPE, etc.)

**Example:**
```csv
run_id,timestamp,model_type,metrics
1962ebc5-a0a1-4aa3-89ff-c748825353f0,2026-01-04T17:40:13.556325,catboost,"{'mae': 0.0, 'wape': 0.0, 'model_type': 'catboost'}"
```

---

## Data Flow

1. **Input**: `sample_sales_input.csv` → Loaded into `daily_item_sales` table
2. **Processing**: Features are built (lags, rolling averages, calendar features)
3. **Training**: Model is trained on historical data
4. **Output**: `sample_forecasts_output.csv` → Generated and stored in `forecasts` table

## Using This Data

To load sample data into your database:

```python
from src.ingest.load_sales import create_sample_data
import yaml

config = yaml.safe_load(open('config/config.yaml'))
create_sample_data(config, num_items=3, days=60)
```

To view data in the database:

```bash
python src/utils/view_data.py --all
```

## Data Format Requirements

### Input Sales Data
- **Date format**: YYYY-MM-DD (ISO 8601)
- **Item ID**: Must exist in `items` table
- **Quantity**: Non-negative number (can be float for partial units)
- **Completeness**: Ideally, all items should have data for all dates (missing dates will be handled gracefully)

### Output Forecasts
- **Date format**: YYYY-MM-DD
- **Predicted quantity**: Non-negative float
- **Run ID**: UUID string identifying the forecast run
- **Uniqueness**: Combination of (date, item_id, run_id) must be unique

## Notes

- All sample data is generated programmatically for testing
- Real-world data may have missing dates, outliers, or different patterns
- The model handles missing data gracefully by using zero-filling for lags
- Forecasts are generated for the next N days (default: 7) starting from "today"

