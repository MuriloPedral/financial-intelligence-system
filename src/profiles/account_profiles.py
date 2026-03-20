from __future__ import annotations

import numpy as np
import pandas as pd


IMPULSIVE_CATEGORIES = {"restaurant", "entertainment", "shopping"}


def _normalize_distribution(series: pd.Series) -> dict[str, float]:
    if series.empty:
        return {}

    total = float(series.sum())
    if total <= 0:
        return {}

    return {
        str(index): round(float(value) / total, 4)
        for index, value in series.items()
    }


def _top_hours(hours: pd.Series, top_n: int = 3) -> list[int]:
    if hours.empty:
        return []
    return [int(hour) for hour in hours.value_counts().head(top_n).index.tolist()]


def _estimate_monthly_income(account_transactions: pd.DataFrame, period_days: int) -> float:
    salary_transactions = account_transactions.loc[
        account_transactions["transaction_type"] == "salary_deposit",
        "amount",
    ]
    if not salary_transactions.empty:
        return round(float(salary_transactions.median()), 2)

    incoming_transactions = account_transactions.loc[
        account_transactions["balance_after"] > account_transactions["balance_before"],
        "amount",
    ]
    if incoming_transactions.empty:
        return 0.0

    estimated_income = float(incoming_transactions.sum()) * (30.0 / max(1, period_days))
    return round(estimated_income, 2)


def _build_single_account_profile(account_transactions: pd.DataFrame) -> dict[str, object]:
    ordered_transactions = account_transactions.sort_values("timestamp").reset_index(drop=True)
    normalized_days = ordered_transactions["timestamp"].dt.normalize()
    period_days = max(1, int((normalized_days.max() - normalized_days.min()).days) + 1)
    period_weeks = max(1.0, period_days / 7.0)
    transaction_hours = ordered_transactions["timestamp"].dt.hour
    transaction_gaps = ordered_transactions["timestamp"].diff().dt.total_seconds().div(60).dropna()
    spending_transactions = ordered_transactions.loc[
        ordered_transactions["balance_after"] < ordered_transactions["balance_before"]
    ].copy()
    amount_to_balance_ratio = (
        ordered_transactions["amount"]
        / ordered_transactions["balance_before"].replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan)

    # Distribuicoes comportamentais
    transaction_type_distribution = _normalize_distribution(
        ordered_transactions["transaction_type"].value_counts(),
    )
    location_distribution = _normalize_distribution(
        ordered_transactions["location"].value_counts(),
    )
    hour_distribution = _normalize_distribution(
        transaction_hours.value_counts().sort_index(),
    )
    spending_category_amount_share = _normalize_distribution(
        spending_transactions.groupby("merchant_category")["amount"].sum().sort_values(ascending=False),
    )
    spending_category_count_share = _normalize_distribution(
        spending_transactions["merchant_category"].value_counts(),
    )

    # Padroes principais
    most_common_transaction_type = (
        ordered_transactions["transaction_type"].mode().iat[0]
        if not ordered_transactions["transaction_type"].mode().empty
        else "unknown"
    )
    home_location = (
        ordered_transactions["location"].mode().iat[0]
        if not ordered_transactions["location"].mode().empty
        else "unknown"
    )
    usual_activity_hours = _top_hours(transaction_hours)
    most_common_spending_category = (
        next(iter(spending_category_amount_share))
        if spending_category_amount_share
        else "no_spending_pattern"
    )

    # Indicadores financeiros
    estimated_monthly_income = _estimate_monthly_income(ordered_transactions, period_days)
    average_monthly_spend = round(
        float(spending_transactions["amount"].sum()) * (30.0 / max(1, period_days)),
        2,
    )
    spend_to_income_ratio = (
        round(average_monthly_spend / estimated_monthly_income, 4)
        if estimated_monthly_income > 0
        else 0.0
    )
    impulsive_spending_share = round(
        sum(spending_category_amount_share.get(category, 0.0) for category in IMPULSIVE_CATEGORIES),
        4,
    )

    return {
        "account_id": str(ordered_transactions["account_id"].iat[0]),
        "analysis_start": ordered_transactions["timestamp"].min(),
        "analysis_end": ordered_transactions["timestamp"].max(),
        "period_days": period_days,
        "transaction_count": int(len(ordered_transactions)),
        "active_days": int(normalized_days.nunique()),
        "active_weeks": int(ordered_transactions["timestamp"].dt.to_period("W").nunique()),
        "mean_amount": round(float(ordered_transactions["amount"].mean()), 2),
        "amount_std": round(float(ordered_transactions["amount"].std(ddof=0)), 2),
        "median_amount": round(float(ordered_transactions["amount"].median()), 2),
        "avg_daily_transactions": round(float(len(ordered_transactions)) / period_days, 2),
        "avg_weekly_transactions": round(float(len(ordered_transactions)) / period_weeks, 2),
        "most_common_transaction_type": most_common_transaction_type,
        "transaction_type_distribution": transaction_type_distribution,
        "most_common_spending_category": most_common_spending_category,
        "spending_category_amount_share": spending_category_amount_share,
        "spending_category_count_share": spending_category_count_share,
        "category_diversity": int(len(spending_category_amount_share)),
        "usual_activity_hours": usual_activity_hours,
        "median_activity_hour": round(float(transaction_hours.median()), 2),
        "hour_distribution": hour_distribution,
        "home_location": home_location,
        "location_distribution": location_distribution,
        "mean_gap_minutes": round(float(transaction_gaps.mean()), 2) if not transaction_gaps.empty else 0.0,
        "gap_std_minutes": round(float(transaction_gaps.std(ddof=0)), 2) if not transaction_gaps.empty else 0.0,
        "mean_amount_to_balance_ratio": round(float(amount_to_balance_ratio.mean(skipna=True)), 4)
        if not amount_to_balance_ratio.dropna().empty
        else 0.0,
        "std_amount_to_balance_ratio": round(float(amount_to_balance_ratio.std(ddof=0, skipna=True)), 4)
        if not amount_to_balance_ratio.dropna().empty
        else 0.0,
        "estimated_monthly_income": estimated_monthly_income,
        "average_monthly_spend": average_monthly_spend,
        "spend_to_income_ratio": spend_to_income_ratio,
        "impulsive_spending_share": impulsive_spending_share,
    }


def build_account_profiles(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame()

    ordered_transactions = transactions.copy().sort_values(["account_id", "timestamp"]).reset_index(drop=True)
    profile_rows = []
    for _, account_transactions in ordered_transactions.groupby("account_id", sort=False):
        profile_rows.append(_build_single_account_profile(account_transactions))

    return pd.DataFrame(profile_rows).sort_values("account_id").reset_index(drop=True)


def build_account_profile_lookup(account_profiles: pd.DataFrame) -> dict[str, dict[str, object]]:
    if account_profiles.empty:
        return {}

    indexed_profiles = account_profiles.set_index("account_id", drop=False)
    return indexed_profiles.to_dict(orient="index")
