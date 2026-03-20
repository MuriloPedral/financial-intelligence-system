from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import DEFAULT_ACCOUNTS_PATH
from src.utils.random_utils import build_rng, normalize_weights, sample_without_replacement


SPENDING_CATEGORIES = [
    "groceries",
    "restaurant",
    "transport",
    "entertainment",
    "utilities",
    "health",
    "shopping",
    "travel",
]

CITY_WEIGHTS = {
    "Aracaju": 0.44,
    "Sao Cristovao": 0.12,
    "Barra dos Coqueiros": 0.10,
    "Nossa Senhora do Socorro": 0.12,
    "Estancia": 0.08,
    "Itabaiana": 0.07,
    "Lagarto": 0.07,
}

ACTIVITY_WEIGHTS = {"low": 0.28, "medium": 0.50, "high": 0.22}
ACTIVITY_RANGES = {"low": (2, 3), "medium": (4, 6), "high": (7, 10)}

SALARY_BANDS = (
    ("low", 1800.0, 3200.0, 0.48),
    ("medium", 3200.0, 7800.0, 0.37),
    ("high", 7800.0, 16500.0, 0.15),
)

ACTIVE_WINDOWS = {
    "day": (6, 20),
    "mixed": (8, 23),
    "night": (18, 3),
}


def _choose_home_city(rng) -> str:
    cities = list(CITY_WEIGHTS.keys())
    weights = list(CITY_WEIGHTS.values())
    return rng.choices(cities, weights=weights, k=1)[0]


def _choose_activity_profile(rng) -> tuple[str, int]:
    levels = list(ACTIVITY_WEIGHTS.keys())
    weights = list(ACTIVITY_WEIGHTS.values())
    activity_level = rng.choices(levels, weights=weights, k=1)[0]
    tx_min, tx_max = ACTIVITY_RANGES[activity_level]
    return activity_level, rng.randint(tx_min, tx_max)


def _generate_salary(rng) -> float:
    salary_band = rng.choices(
        [band_name for band_name, *_ in SALARY_BANDS],
        weights=[weight for *_, weight in SALARY_BANDS],
        k=1,
    )[0]

    for band_name, lower_bound, upper_bound, _ in SALARY_BANDS:
        if salary_band == band_name:
            return round(rng.uniform(lower_bound, upper_bound), 2)

    msg = "Nao foi possivel determinar a faixa salarial."
    raise RuntimeError(msg)


def _generate_category_weights(rng) -> dict[str, float]:
    favorite_categories = sample_without_replacement(SPENDING_CATEGORIES, sample_size=3, rng=rng)
    raw_weights = {category: rng.uniform(0.2, 1.0) for category in favorite_categories}
    normalized = normalize_weights(raw_weights)
    return {category: round(weight, 4) for category, weight in normalized.items()}


def generate_account(account_number: int, seed: int | None = None) -> dict[str, object]:
    rng = build_rng(seed if seed is not None else account_number)
    salary = _generate_salary(rng)
    activity_level, transactions_per_day = _choose_activity_profile(rng)
    active_profile = rng.choices(["day", "mixed", "night"], weights=[0.56, 0.30, 0.14], k=1)[0]
    active_hour_start, active_hour_end = ACTIVE_WINDOWS[active_profile]
    initial_balance = round(salary * rng.uniform(0.8, 3.4), 2)

    return {
        "account_id": f"A{account_number:05d}",
        "home_city": _choose_home_city(rng),
        "initial_balance": initial_balance,
        "current_balance": initial_balance,
        "salary": salary,
        "salary_day": rng.randint(1, 5),
        "activity_level": activity_level,
        "transactions_per_day": transactions_per_day,
        "favorite_categories": _generate_category_weights(rng),
        "active_hour_start": active_hour_start,
        "active_hour_end": active_hour_end,
    }


def generate_accounts(accounts_count: int, seed: int | None = None) -> list[dict[str, object]]:
    master_rng = build_rng(seed)
    accounts = []
    for index in range(1, accounts_count + 1):
        account_seed = master_rng.randint(1, 10_000_000)
        accounts.append(generate_account(index, seed=account_seed))
    return accounts


def accounts_to_frame(accounts: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(accounts)
    if "favorite_categories" in frame.columns:
        frame["favorite_categories"] = frame["favorite_categories"].apply(
            lambda value: json.dumps(value, sort_keys=True),
        )
    return frame


def sync_account_balances(
    accounts: list[dict[str, object]],
    transactions: list[dict[str, object]] | pd.DataFrame,
) -> list[dict[str, object]]:
    if isinstance(transactions, pd.DataFrame):
        transactions_frame = transactions.copy()
    else:
        transactions_frame = pd.DataFrame(transactions)

    if transactions_frame.empty:
        return accounts

    final_balances = (
        transactions_frame.sort_values(["account_id", "timestamp"])
        .groupby("account_id", sort=False)["balance_after"]
        .last()
        .to_dict()
    )

    for account in accounts:
        account_id = str(account["account_id"])
        if account_id in final_balances:
            account["current_balance"] = round(float(final_balances[account_id]), 2)

    return accounts


def validate_accounts(accounts: list[dict[str, object]] | pd.DataFrame) -> None:
    accounts_frame = accounts.copy() if isinstance(accounts, pd.DataFrame) else accounts_to_frame(accounts)
    if accounts_frame.empty:
        msg = "O dataset de contas gerado esta vazio."
        raise ValueError(msg)
    if accounts_frame["account_id"].duplicated().any():
        msg = "Foram encontrados account_id duplicados no dataset de contas."
        raise ValueError(msg)

    required_columns = {"account_id", "initial_balance", "current_balance", "salary", "favorite_categories"}
    missing_columns = required_columns.difference(accounts_frame.columns)
    if missing_columns:
        formatted_columns = ", ".join(sorted(missing_columns))
        msg = f"O dataset de contas nao possui as colunas obrigatorias: {formatted_columns}"
        raise ValueError(msg)


def save_accounts(accounts: list[dict[str, object]], output_path: Path | None = None) -> Path:
    resolved_path = output_path or DEFAULT_ACCOUNTS_PATH
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    accounts_to_frame(accounts).to_csv(resolved_path, index=False)
    return resolved_path
