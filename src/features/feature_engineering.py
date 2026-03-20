from __future__ import annotations

import numpy as np
import pandas as pd


def engineer_transaction_features(transactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    enriched_transactions = transactions.copy().sort_values(["account_id", "timestamp"]).reset_index(drop=True)
    grouped = enriched_transactions.groupby("account_id", sort=False)

    enriched_transactions["hour"] = enriched_transactions["timestamp"].dt.hour
    enriched_transactions["day_of_week"] = enriched_transactions["timestamp"].dt.dayofweek
    enriched_transactions["day_of_month"] = enriched_transactions["timestamp"].dt.day
    enriched_transactions["is_weekend"] = (enriched_transactions["day_of_week"] >= 5).astype(int)
    enriched_transactions["amount_log"] = np.log1p(enriched_transactions["amount"])
    enriched_transactions["balance_change"] = (
        enriched_transactions["balance_after"] - enriched_transactions["balance_before"]
    )
    enriched_transactions["balance_delta_ratio"] = (
        enriched_transactions["balance_change"]
        / enriched_transactions["balance_before"].replace(0, np.nan)
    )
    enriched_transactions["amount_to_balance_ratio"] = (
        enriched_transactions["amount"]
        / enriched_transactions["balance_before"].replace(0, np.nan)
    )
    enriched_transactions["account_transaction_count"] = grouped["transaction_id"].transform("count")
    enriched_transactions["account_mean_amount"] = grouped["amount"].transform("mean")
    enriched_transactions["account_std_amount"] = grouped["amount"].transform("std").fillna(0.0)
    enriched_transactions["account_median_amount"] = grouped["amount"].transform("median")
    enriched_transactions["account_max_amount"] = grouped["amount"].transform("max")
    enriched_transactions["account_amount_p90"] = grouped["amount"].transform(lambda values: values.quantile(0.90))
    enriched_transactions["amount_vs_account_mean"] = (
        enriched_transactions["amount"]
        / enriched_transactions["account_mean_amount"].replace(0, np.nan)
    )
    enriched_transactions["amount_vs_account_p90"] = (
        enriched_transactions["amount"]
        / enriched_transactions["account_amount_p90"].replace(0, np.nan)
    )
    enriched_transactions["transaction_gap_minutes"] = (
        grouped["timestamp"].diff().dt.total_seconds().div(60).fillna(0.0)
    )
    enriched_transactions["is_night_transaction"] = (
        (enriched_transactions["hour"] <= 5) | (enriched_transactions["hour"] >= 23)
    ).astype(int)

    home_location = grouped["location"].transform(
        lambda values: values.mode().iat[0] if not values.mode().empty else values.iloc[0],
    )
    median_active_hour = grouped["hour"].transform("median")
    enriched_transactions["home_location_proxy"] = home_location
    enriched_transactions["is_unusual_location"] = (
        enriched_transactions["location"] != enriched_transactions["home_location_proxy"]
    ).astype(int)
    enriched_transactions["distance_from_usual_hour"] = (
        enriched_transactions["hour"] - median_active_hour
    ).abs()
    enriched_transactions["is_large_transaction"] = (
        enriched_transactions["amount"] > enriched_transactions["account_amount_p90"]
    ).astype(int)

    feature_columns = [
        "amount",
        "amount_log",
        "balance_before",
        "balance_after",
        "balance_change",
        "balance_delta_ratio",
        "amount_to_balance_ratio",
        "account_transaction_count",
        "account_mean_amount",
        "account_std_amount",
        "account_median_amount",
        "account_max_amount",
        "amount_vs_account_mean",
        "amount_vs_account_p90",
        "transaction_gap_minutes",
        "hour",
        "day_of_week",
        "day_of_month",
        "is_weekend",
        "is_night_transaction",
        "is_unusual_location",
        "distance_from_usual_hour",
        "is_large_transaction",
        "transaction_type",
        "merchant_category",
        "transaction_channel",
        "location",
    ]

    feature_matrix = pd.get_dummies(
        enriched_transactions[feature_columns],
        columns=["transaction_type", "merchant_category", "transaction_channel", "location"],
        dtype=float,
    )
    feature_matrix = feature_matrix.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return enriched_transactions, feature_matrix
