# Financial Intelligence System

Synthetic data and financial intelligence project for simulating accounts, analyzing transactions, detecting suspicious behavior, and generating account-level recommendations.

## Overview

This project creates a synthetic financial environment and applies behavioral analytics on top of it. The operational flow now relies only on internally generated data.

The system currently does four main things:

1. generates synthetic bank accounts with financial behavior patterns
2. generates synthetic transaction histories with normal and suspicious activity
3. detects and explains anomalous transactions
4. generates personalized financial recommendations per account

## System flow

The regular workflow happens in two commands:

1. `python run_generation.py`
   generates synthetic accounts and transactions into `data/raw/generated/`

2. `python main.py`
   loads only the internally generated synthetic dataset, builds features, builds account profiles, detects anomalies, explains them, and exports the analytical reports

Important:

- the main flow no longer accepts external transaction CSV files
- analysis always uses `data/raw/generated/transactions.csv`

## Main structure

```text
financial-intelligence-system/
  data/
    raw/
      generated/
        accounts.csv
        transactions.csv
    reports/
      account_profiles.csv
      anomaly_report.csv
      financial_recommendations.csv
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
  DOCUMENTO-DO-PROJETO.md
```

## What each stage does

### 1. Synthetic generation

In [run_generation.py](C:/Users/muril/Códigos/financial-intelligence-system/run_generation.py), the system:

1. creates accounts with salary, initial balance, city, favorite categories, and active hours
2. simulates salary deposits, PIX transfers, purchases, bill payments, and withdrawals
3. injects suspicious behavior in a controlled way
4. validates IDs, balances, and continuity
5. saves the raw CSV files

### 2. Financial analysis

In [main.py](C:/Users/muril/Códigos/financial-intelligence-system/main.py), the system:

1. loads the internally generated dataset
2. validates schema and data types
3. builds behavioral features
4. builds an explicit financial profile for each account
5. runs Isolation Forest
6. explains detected anomalies
7. generates actionable financial recommendations
8. exports the final analytical reports

## Final reports

### `anomaly_report.csv`

This file is now cleaner:

- it contains only transactions classified as anomalies
- it avoids exporting all internal model features
- it prioritizes human-readable columns

Key fields:

- `anomaly_rank`
- `transaction_id`
- `account_id`
- `timestamp`
- `transaction_type`
- `amount`
- `anomaly_score`
- `anomaly_explanation`

### `account_profiles.csv`

One consolidated row per account focused on financial behavior.

Key fields:

- `mean_amount`
- `amount_std`
- `avg_daily_transactions`
- `avg_weekly_transactions`
- `estimated_monthly_income`
- `average_monthly_spend`
- `spend_to_income_ratio`
- `impulsive_spending_share`

### `financial_recommendations.csv`

Now exports only actionable recommendations, avoiding repetitive rows with low practical value.

Key fields:

- `recommendation_rank`
- `account_id`
- `top_spending_category`
- `spend_to_income_ratio`
- `recommendation_priority`
- `recommendations_text`

## Terminal output

Terminal output was reorganized to be easier to read.

Generation now shows:

- simulated period
- number of accounts
- number of transactions
- average transactions per account
- labeled fraud count
- generated file paths

Analysis now shows:

- analyzed source
- analysis period
- total volume analyzed
- detected and explained anomalies
- accounts with actionable recommendations
- saved report paths
- top anomalies
- highlighted recommendations

## How to run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate synthetic data

```bash
python run_generation.py --accounts 150 --months 6 --seed 42
```

### 3. Run analysis

```bash
python main.py --top-n 10
```

## Main modules

- [src/generators/account_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/generators/account_generator.py)
  account generation

- [src/generators/transaction_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/generators/transaction_generator.py)
  transaction generation

- [src/features/feature_engineering.py](C:/Users/muril/Códigos/financial-intelligence-system/src/features/feature_engineering.py)
  model features

- [src/profiles/account_profiles.py](C:/Users/muril/Códigos/financial-intelligence-system/src/profiles/account_profiles.py)
  account financial profiles

- [src/explainability/anomaly_explainer.py](C:/Users/muril/Códigos/financial-intelligence-system/src/explainability/anomaly_explainer.py)
  anomaly explainability

- [src/recommendations/financial_recommendations.py](C:/Users/muril/Códigos/financial-intelligence-system/src/recommendations/financial_recommendations.py)
  financial recommendations

- [src/reporting/report_generator.py](C:/Users/muril/Códigos/financial-intelligence-system/src/reporting/report_generator.py)
  report export and terminal formatting

## Main project document

For a fuller explanation of purpose, scope, architecture, and limitations, see [DOCUMENTO-DO-PROJETO.md](C:/Users/muril/Códigos/financial-intelligence-system/DOCUMENTO-DO-PROJETO.md).
