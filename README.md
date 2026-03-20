# Financial Intelligence System

Synthetic financial data, behavioral analysis, anomaly explainability, and account-level financial recommendations.

## Overview

This project simulates a plausible financial environment and turns transaction history into actionable intelligence.

The system currently does four main things:

1. generates synthetic bank accounts with behavioral patterns
2. generates transaction histories with normal and suspicious behavior
3. detects anomalous transactions with Isolation Forest
4. produces anomaly explanations and personalized financial recommendations

The result is no longer just an anomaly detector. It is a small financial intelligence platform built around simulated data.

## End-to-end pipeline

When the full flow runs, the system follows this order:

1. creates synthetic accounts with salary, balance, city, active hours, and spending preferences
2. simulates transaction history for each account
3. validates dataset integrity
4. loads the transaction dataset
5. builds modeling features
6. builds an explicit financial profile for each account
7. runs Isolation Forest
8. explains each anomaly by comparing the transaction to the account profile
9. creates personalized financial recommendations per account
10. exports reports and prints a structured terminal summary

## What the project delivers

### Synthetic data generation

- account generation with income, balance, and spending preferences
- transaction generation with salary deposits, PIX transfers, purchases, bill payments, and withdrawals
- suspicious behavior injection for model evaluation

### Behavioral analysis

- account-level feature engineering
- anomaly detection with Isolation Forest
- normalized anomaly scoring
- ranked suspicious transaction output

### Financial intelligence

- explicit financial profiles per account
- readable anomaly explanations
- simple personalized financial recommendations

## Main structure

```text
financial-intelligence-system/
  data/
    raw/
      generated/
    reports/
  src/
    dataset/
    explainability/
    features/
    generators/
    models/
    profiles/
    recommendations/
    reporting/
    utils/
  main.py
  run_generation.py
  requirements.txt
```

## Module responsibilities

- `run_generation.py`
  Orchestrates synthetic account and transaction generation.

- `main.py`
  Orchestrates the full analytical pipeline: loading, features, profiles, model, explanations, recommendations, and reports.

- `src/config.py`
  Central place for paths and runtime configuration.

- `src/generators/account_generator.py`
  Builds the base synthetic account profile.

- `src/generators/transaction_generator.py`
  Simulates transactions and preserves balance continuity.

- `src/dataset/load_dataset.py`
  Loads CSV files and validates the minimum required schema.

- `src/features/feature_engineering.py`
  Builds model-ready behavioral features.

- `src/profiles/account_profiles.py`
  Builds the explicit financial profile for each account, including averages, standard deviation, frequency, category mix, and activity hours.

- `src/models/anomaly_detection.py`
  Runs Isolation Forest and returns anomaly score and anomaly flag.

- `src/explainability/anomaly_explainer.py`
  Explains each anomaly with readable rules based on the account profile.

- `src/recommendations/financial_recommendations.py`
  Generates personalized financial recommendations from the account behavior history.

- `src/reporting/report_generator.py`
  Exports the final CSV files and formats the Portuguese terminal output.

## How generation works

When you run `python run_generation.py`, the project:

1. ensures the `data/` folders exist
2. builds the generation configuration
3. creates synthetic accounts
4. simulates transactions within the selected period
5. updates balances before and after each operation
6. validates dataset integrity
7. saves:
   - `data/raw/generated/accounts.csv`
   - `data/raw/generated/transactions.csv`

## How analysis works

When you run `python main.py`, the project:

1. resolves the input dataset
2. validates columns and types
3. builds modeling features
4. builds an account-level financial profile with:
   - average transaction amount
   - transaction amount standard deviation
   - daily and weekly transaction frequency
   - spending category distribution
   - most common activity hours
   - most common transaction types
5. runs Isolation Forest
6. explains anomalous transactions with readable rules
7. builds personalized financial recommendations
8. saves:
   - `data/reports/anomaly_report.csv`
   - `data/reports/account_profiles.csv`
   - `data/reports/financial_recommendations.csv`

## Report outputs

### `anomaly_report.csv`

One row per analyzed transaction with anomaly score, anomaly flag, and explanation fields.

Important fields:

- `anomaly_score`
- `raw_anomaly_score`
- `is_anomaly`
- `anomaly_explanation`
- `explanation_count`

### `account_profiles.csv`

One row per account with the explicit financial profile.

Important fields:

- `mean_amount`
- `amount_std`
- `avg_daily_transactions`
- `avg_weekly_transactions`
- `transaction_type_distribution`
- `spending_category_amount_share`
- `usual_activity_hours`
- `estimated_monthly_income`
- `average_monthly_spend`

### `financial_recommendations.csv`

One row per account with personalized recommendation output.

Important fields:

- `top_spending_category`
- `top_spending_share`
- `spend_to_income_ratio`
- `impulsive_spending_share`
- `recommendations_text`
- `recommendation_count`

## How to run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate synthetic data

```bash
python run_generation.py --accounts 150 --months 6 --seed 42
```

### 3. Run the full analysis

```bash
python main.py
```

### 4. Run with a custom CSV

```bash
python main.py --input-path data/raw/financial_transactions.csv --top-n 15
```

This command is useful when you want to analyze an external CSV without relying on the locally generated synthetic dataset.

## Minimum columns required for a custom transaction CSV

If you want to use your own file, the pipeline expects at least these columns:

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
- `origin_account`
- `destination_account`

## Terminal output

The terminal experience was redesigned to be more explanatory.

Generation output shows:

- simulated period
- number of accounts
- number of transactions
- number of labeled frauds
- generated file paths

Analysis output shows:

- analyzed dataset
- number of accounts and transactions
- generated financial profiles
- detected and explained anomalies
- paths for the three final reports
- ranked suspicious transactions with explanation
- highlighted financial recommendations

## Codebase note

Function names, classes, and variables remain in English to preserve a common technical convention, but:

- terminal output is in Portuguese
- code comments were expanded for study purposes
- the documentation is now more process-oriented

## Tests

The project includes tests in `tests/test_pipeline_integrity.py` covering:

- account and transaction balance consistency
- `pix_out` category consistency
- safe anomaly detection behavior on very small datasets
- financial profile construction
- anomaly explanation generation
- recommendation generation

## Author

Murilo Pedral
