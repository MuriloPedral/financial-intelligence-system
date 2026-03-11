# Financial Intelligence System

## Overview

The **Financial Intelligence System** is a project designed to simulate financial behavior and detect anomalies in transaction data.

The goal is to build a synthetic financial dataset and develop analytical tools capable of identifying unusual patterns such as fraudulent transactions or abnormal account behavior.

This project is being developed as a **learning-oriented system**, focusing on:

* Data simulation
* Behavioral modeling
* Anomaly detection
* Financial transaction analysis

The system generates synthetic banking data including **accounts and transactions** that mimic realistic financial behavior.

---

# Project Goals

The main goals of the project are:

* Generate a **synthetic financial dataset**
* Simulate **bank accounts with behavioral profiles**
* Simulate **daily financial transactions**
* Inject **anomalous behavior**
* Build **tools for anomaly detection**

The dataset will contain information such as:

* accounts
* transactions
* transaction timestamps
* transaction types
* transaction locations
* account balances
* fraud indicators

---

# Dataset Design

The simulated dataset will contain two main entities:

## Accounts

Each account represents a simulated bank user with behavioral characteristics.

Example fields:

* `account_id`
* `home_city`
* `initial_balance`
* `current_balance`
* `salary`
* `activity_level`
* `transactions_per_day`
* `favorite_categories`
* `active_hour_start`
* `active_hour_end`

These attributes define **how the account behaves financially**.

---

## Transactions

Transactions simulate the financial activity of each account over time.

Example fields:

* `transaction_id`
* `account_id`
* `timestamp`
* `transaction_type`
* `amount`
* `balance_before`
* `balance_after`
* `merchant_category`
* `transaction_channel`
* `location`
* `is_fraud`
* `origin_account`
* `destination_account`

---

# Current Development Stage

The project is currently in the **data generation phase**.

The first module implemented is:

### Account Generator

This module creates synthetic bank accounts with realistic attributes.

Each generated account includes:

* salary-based balance
* financial activity level
* daily transaction frequency
* preferred spending categories
* active hours for transactions
* home city

Example generated account:

```json
{
  "account_id": 1,
  "home_city": "Aracaju",
  "initial_balance": 5400,
  "current_balance": 5400,
  "salary": 3200,
  "activity_level": "medium",
  "transactions_per_day": 5,
  "favorite_categories": {
    "groceries": 0.52,
    "transport": 0.31,
    "restaurant": 0.17
  },
  "active_hour_start": 8,
  "active_hour_end": 20
}
```

---

# Project Structure

```
financial-intelligence-system/

data/
    generated/

src/
    generators/

        account_generator.py
        transaction_generator.py

README.md
```

---

# Next Development Steps

The next module to be implemented is the **Transaction Generator**, responsible for simulating daily financial activity.

The generator will:

* simulate transactions over **6 months**
* generate **2 to 10 transactions per day per account**
* update account balances
* simulate merchant categories
* simulate transaction channels
* generate transaction timestamps
* inject anomalous patterns

This will produce a dataset with **thousands of realistic financial transactions**.

---

# Future Work

Planned improvements include:

* anomaly injection module
* statistical analysis of financial behavior
* anomaly detection models
* visualization dashboards
* fraud detection experiments

---

# Technologies

The project is currently implemented using:

* Python
* Randomized data simulation
* Structured dataset generation

Future tools may include:

* Pandas
* PostgreSQL
* Machine Learning models
* Data visualization tools

---

# Author

Murilo Pedral

Computer Science student exploring data simulation, anomaly detection and financial data modeling.
