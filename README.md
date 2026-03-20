# Financial Intelligence System

Synthetic financial data generation and anomaly detection project for suspicious transaction analysis.

## Project idea

This project simulates a fictional banking environment and then applies data analysis and machine learning to detect unusual financial behavior.

Instead of depending on real banking data, the system creates:

1. synthetic bank accounts with behavior profiles
2. realistic transaction histories
3. injected anomalous behavior
4. a final ranked report of suspicious transactions

The result is a practical end-to-end project that combines data generation, feature engineering, anomaly detection, and reporting.

## What the system delivers today

The repository currently has two main stages:

1. Synthetic data generation
2. Anomaly detection analysis

The end-to-end flow works like this:

1. the system creates accounts with salary, balance, city, active hours, and favorite spending categories
2. the system simulates daily transactions for each account
3. each transaction receives amount, type, location, balance before, and balance after
4. some transactions are generated with abnormal behavior to mimic suspicious activity
5. the analytical pipeline loads the CSV
6. the pipeline builds behavioral features per account
7. Isolation Forest calculates anomaly scores
8. the system exports a final CSV with the ranked suspicious transactions

## Main project structure

```text
financial-intelligence-system/
  data/
    raw/
      generated/
    reports/
  src/
    dataset/
    features/
    generators/
    models/
    reporting/
    utils/
  main.py
  run_generation.py
  requirements.txt
```

## What each part does

- `run_generation.py`
  Main script for synthetic account and transaction generation.

- `main.py`
  Main script for dataset loading, feature engineering, anomaly detection, and reporting.

- `src/config.py`
  Central place for paths and runtime configuration.

- `src/generators/account_generator.py`
  Creates synthetic account profiles.

- `src/generators/transaction_generator.py`
  Simulates transactions and account balance evolution over time.

- `src/dataset/load_dataset.py`
  Loads CSV files and validates the required schema.

- `src/features/feature_engineering.py`
  Builds model-ready features from raw transactions.

- `src/models/anomaly_detection.py`
  Runs Isolation Forest and produces anomaly scores.

- `src/reporting/report_generator.py`
  Formats the terminal summary and exports the final report.

## How generation works

When you run `python run_generation.py`, the project does the following:

1. creates the required folders inside `data/`
2. builds a configuration object with account count, months, fraud rate, and seed
3. generates synthetic account profiles
4. simulates a full period of transactions for each account
5. includes salary deposits, transfers, purchases, bill payments, and withdrawals
6. updates the account balance after every transaction
7. validates the generated datasets for duplicate IDs and balance consistency
8. saves:
   - `data/raw/generated/accounts.csv`
   - `data/raw/generated/transactions.csv`

## How analysis works

When you run `python main.py`, the project does the following:

1. finds the dataset to analyze
2. validates the file structure
3. converts columns to the correct data types
4. creates features such as:
   - transaction hour
   - day of week
   - amount relative to the balance
   - amount compared to the account mean
   - time between transactions
   - unusual location
   - unusual hour
5. applies Isolation Forest
6. generates:
   - `anomaly_score`
   - `raw_anomaly_score`
   - `is_anomaly`
7. saves the result to `data/reports/anomaly_report.csv`
8. prints a terminal summary with the most suspicious transactions

## How to run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate synthetic data

```bash
python run_generation.py --accounts 150 --months 6 --seed 42
```

### 3. Run anomaly analysis

```bash
python main.py
```

### 4. Run with a custom CSV

```bash
python main.py --input-path data/raw/financial_transactions.csv --top-n 15
```

## What is inside the CSV files

### Accounts file

Each account includes fields such as:

- `account_id`
- `home_city`
- `initial_balance`
- `current_balance`
- `salary`
- `salary_day`
- `activity_level`
- `transactions_per_day`
- `favorite_categories`
- `active_hour_start`
- `active_hour_end`

### Transactions file

Each transaction includes fields such as:

- `transaction_id`
- `account_id`
- `timestamp`
- `transaction_type`
- `amount`
- `balance_before`
- `balance_after`
- `merchant_category`
- `transaction_channel`
- `location`
- `is_fraud`
- `origin_account`
- `destination_account`

## Terminal output

The scripts now print clearer terminal summaries.

Generation output includes:

- simulated period
- generated accounts
- generated transactions
- transactions labeled as fraud
- generated file paths
- next suggested command

Analysis output includes:

- input dataset path
- analyzed transactions
- analyzed accounts
- detected anomalies
- labeled frauds in the dataset
- labeled frauds found by the model
- final report path
- ranked suspicious transactions

## Important note about the codebase

Function names, classes, and variable names stay in English to preserve a common technical convention, but:

- terminal messages are in Portuguese
- code comments were expanded for study purposes
- the documentation is now more didactic

## Tests and validation

The project includes tests in `tests/test_pipeline_integrity.py` to validate:

- account final balance consistency
- `pix_out` category consistency
- safe anomaly detection behavior on very small datasets

## Author

Murilo Pedral
