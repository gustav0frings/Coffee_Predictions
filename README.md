# Sales Forecasting (Local, SQLite)

## Purpose

This project forecasts daily sales per item for the next 7 days using historical sales data.

It is designed to be:

- **Local-first**
- **Simple to run**
- **Deterministic**
- **Easy to migrate later to Supabase**

## What it does

- Ingests raw sales data
- Aggregates sales daily per item
- Builds time-series features (lags, rolling averages)
- Trains a global ML model
- Generates next-week forecasts
- Stores results in SQLite

## What it does NOT do

- No real-time prediction
- No dashboard (yet)
- No automatic posting or ordering logic

## Tech stack

- Python 3.11
- SQLite (local database)
- Pandas / NumPy
- ML: CatBoost or LightGBM
- Tooling: uv (Python + deps)
- OS: macOS (primary), Windows compatible

## Environment setup (macOS)

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal.

### Install Python 3.11

```bash
uv python install 3.11
uv python pin 3.11
```

This will create a `.python-version` file pinning the project to Python 3.11.

### Create virtual environment

```bash
uv venv
source .venv/bin/activate
```

The virtual environment will automatically use Python 3.11.

### Install dependencies

```bash
uv pip install pandas numpy scikit-learn catboost lightgbm matplotlib pyyaml sqlite-utils joblib
```

Or install from project:

```bash
uv pip install -e .
```

**Note on ML libraries:**
- **CatBoost**: Works out of the box on Python 3.11
- **LightGBM**: Requires `libomp` system library. Install with `brew install libomp` if you encounter import errors. The code will gracefully fall back to scikit-learn's RandomForestRegressor if LightGBM is unavailable.
- **Fallback**: If neither CatBoost nor LightGBM are available, the system automatically uses scikit-learn's RandomForestRegressor.

## Running the project

Make sure you're in the project root and have activated the virtual environment:

```bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)  # Or use: PYTHONPATH=$(pwd) python src/run_pipeline.py
```

### Run full pipeline (forecast only)

```bash
python src/run_pipeline.py --mode predict
```

### Retrain model + forecast

```bash
python src/run_pipeline.py --mode retrain
```

### Generate sample data (for testing)

To create sample sales data for testing:

```bash
python -c "from src.ingest.load_sales import create_sample_data; import yaml; config = yaml.safe_load(open('config/config.yaml')); create_sample_data(config, num_items=3, days=60)"
```

## Project Structure

```
.
├── data/
│   └── forecast.db            # SQLite database (created at runtime)
├── config/
│   └── config.yaml            # paths + model settings
├── src/
│   ├── ingest/
│   │   └── load_sales.py      # raw → daily_item_sales
│   ├── features/
│   │   └── build_features.py  # lags, rolling, calendar
│   ├── models/
│   │   ├── train.py           # model training
│   │   └── predict.py         # next-week prediction
│   ├── utils/
│   │   ├── db.py              # SQLite helpers
│   │   ├── metrics.py         # MAE, WAPE
│   │   └── dates.py           # date logic
│   └── run_pipeline.py        # main entry point
├── models/
│   └── latest.model           # saved ML model
└── reports/
    └── README.md              # metrics & plots later
```

## Configuration

Edit `config/config.yaml` to customize:

- Database path
- Forecast horizon (default: 7 days)
- Feature window (default: 28 days)
- Model type (`catboost` or `lightgbm`)

The model type will automatically fall back to `RandomForestRegressor` (from scikit-learn) if the requested library is not available.

## Database Schema

The SQLite database (`data/forecast.db`) contains:

- `items`: Item master data
- `daily_item_sales`: Historical daily sales per item
- `forecasts`: Generated forecasts
- `model_runs`: Training run metadata

