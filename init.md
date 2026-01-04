Below is a starter scaffold + README content you can copy-paste to begin the project cleanly.
It is intentionally minimal, intern-friendly, and aligned with the architecture you defined.

No business logic yet, just the bones so work starts correctly.

1) Project scaffold (initial)
forecasting/
│
├── data/
│   └── forecast.db            # SQLite database (created at runtime)
│
├── config/
│   └── config.yaml            # paths + model settings
│
├── src/
│   ├── ingest/
│   │   └── load_sales.py      # raw → daily_item_sales
│   │
│   ├── features/
│   │   └── build_features.py  # lags, rolling, calendar
│   │
│   ├── models/
│   │   ├── train.py           # model training
│   │   └── predict.py         # next-week prediction
│   │
│   ├── utils/
│   │   ├── db.py              # SQLite helpers
│   │   ├── metrics.py         # MAE, WAPE
│   │   └── dates.py           # date logic
│   │
│   └── run_pipeline.py        # main entry point
│
├── models/
│   └── latest.model           # saved ML model
│
├── reports/
│   └── README.md              # metrics & plots later
│
├── pyproject.toml             # linting & tooling
├── .gitignore
└── README.md

2) README – project explanation (starter)
Project: Sales Forecasting (Local, SQLite)
Purpose

This project forecasts daily sales per item for the next 7 days using historical sales data.

It is designed to be:

Local-first

Simple to run

Deterministic

Easy to migrate later to Supabase

What it does

Ingests raw sales data

Aggregates sales daily per item

Builds time-series features (lags, rolling averages)

Trains a global ML model

Generates next-week forecasts

Stores results in SQLite

What it does NOT do

No real-time prediction

No dashboard (yet)

No automatic posting or ordering logic

Tech stack

Python 3.11

SQLite (local database)

Pandas / NumPy

ML: CatBoost or LightGBM

Tooling: uv (Python + deps)

OS: macOS (primary), Windows compatible

Environment setup (macOS)
Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh


Restart your terminal.

Install Python
uv python install 3.11
uv python pin 3.11

Create virtual environment
uv venv
source .venv/bin/activate

Install dependencies
uv pip install pandas numpy scikit-learn catboost lightgbm matplotlib pyyaml sqlite-utils

Running the project
Run full pipeline (forecast only)
python src/run_pipeline.py --mode predict

Retrain model + forecast
python src/run_pipeline.py --mode retrain

3) Basic config file (concept)

config/config.yaml should define:

database path

forecast horizon (7)

feature window (28 days)

model type

retrain flag

No hardcoded paths inside scripts.

4) Script responsibilities (no code, clear intent)
src/models/train.py

Responsibility

Load historical features

Split data using time-based validation

Train global model

Compare vs baselines

Save model artifact

Inputs

Feature dataframe

Config

Outputs

models/latest.model

Metrics (logged or saved)

src/models/predict.py

Responsibility

Load latest model

Build features for next 7 days per item

Generate forecasts

Write results to SQLite

Inputs

Latest sales data

Calendar info

Model artifact

Outputs

forecasts table in SQLite

src/run_pipeline.py

Responsibility

Orchestrate everything

Parse CLI args

Call ingest → features → train → predict

This is the only file you run manually.

5) SQLite expectations (initial)

Database file:

data/forecast.db


Tables expected early:

items

daily_item_sales

forecasts

model_runs (metadata)

You should be able to open it with any SQLite viewer and understand it.

6) Linting & basic quality gates
Minimal but important

Use:

ruff for linting

black for formatting (optional)

Add later:

No unused imports

No functions > ~50 lines

Clear docstrings for scripts

You are optimizing for readability, not cleverness.

7) Definition of “project bootstrapped”

You are ready to start real work when:

Python runs via uv

forecast.db is created

run_pipeline.py executes without error

README is accurate enough that someone else can run it