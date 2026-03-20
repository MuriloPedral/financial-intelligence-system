from __future__ import annotations

import json
from datetime import datetime, time
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DEFAULT_TRANSACTIONS_PATH, GenerationConfig
from src.utils.random_utils import build_rng, choose_weighted
from src.utils.time_utils import date_sequence, random_timestamp


CITY_NETWORK = {
    "Aracaju": ["Sao Cristovao", "Barra dos Coqueiros", "Nossa Senhora do Socorro"],
    "Sao Cristovao": ["Aracaju", "Barra dos Coqueiros"],
    "Barra dos Coqueiros": ["Aracaju", "Sao Cristovao"],
    "Nossa Senhora do Socorro": ["Aracaju", "Sao Cristovao"],
    "Estancia": ["Lagarto", "Aracaju"],
    "Itabaiana": ["Aracaju", "Lagarto"],
    "Lagarto": ["Estancia", "Aracaju"],
}

TRAVEL_CITIES = [
    "Salvador",
    "Maceio",
    "Recife",
    "Fortaleza",
    "Sao Paulo",
    "Rio de Janeiro",
    "Belo Horizonte",
]

CATEGORY_AMOUNT_RANGES = {
    "groceries": (18.0, 260.0),
    "restaurant": (18.0, 190.0),
    "transport": (8.0, 85.0),
    "entertainment": (25.0, 260.0),
    "utilities": (55.0, 420.0),
    "health": (30.0, 480.0),
    "shopping": (45.0, 820.0),
    "travel": (160.0, 2200.0),
    "transfer": (30.0, 1500.0),
    "cash_withdrawal": (40.0, 600.0),
}

TYPE_CHANNELS = {
    "card_purchase": ["debit_card", "credit_card", "mobile_wallet"],
    "online_purchase": ["internet_banking", "mobile_app", "card_not_present"],
    "pix_out": ["pix"],
    "pix_in": ["pix"],
    "bill_payment": ["mobile_app", "internet_banking"],
    "atm_withdrawal": ["atm"],
    "salary_deposit": ["bank_transfer"],
}


def _coerce_accounts(accounts: Any) -> list[dict[str, Any]]:
    if isinstance(accounts, pd.DataFrame):
        records = accounts.to_dict("records")
    else:
        records = [dict(account) for account in accounts]

    coerced_accounts = []
    for account in records:
        normalized_account = dict(account)
        favorite_categories = normalized_account.get("favorite_categories", {})
        if isinstance(favorite_categories, str):
            favorite_categories = json.loads(favorite_categories)

        normalized_account["favorite_categories"] = favorite_categories
        normalized_account["salary"] = float(normalized_account["salary"])
        normalized_account["initial_balance"] = float(normalized_account["initial_balance"])
        normalized_account["current_balance"] = float(
            normalized_account.get("current_balance", normalized_account["initial_balance"]),
        )
        normalized_account["transactions_per_day"] = int(normalized_account["transactions_per_day"])
        normalized_account["salary_day"] = int(normalized_account.get("salary_day", 5))
        normalized_account["active_hour_start"] = int(normalized_account["active_hour_start"])
        normalized_account["active_hour_end"] = int(normalized_account["active_hour_end"])
        coerced_accounts.append(normalized_account)

    return coerced_accounts


def _daily_transactions_target(account: dict[str, Any], current_date, rng) -> int:
    base_target = int(account["transactions_per_day"])
    lower_bound = max(1, base_target - 2)
    upper_bound = base_target + 2
    sampled_target = rng.randint(lower_bound, upper_bound)
    if current_date.weekday() >= 5 and account["activity_level"] != "low":
        sampled_target += 1
    return sampled_target


def _pick_spending_category(account: dict[str, Any], is_fraud: bool, rng) -> str:
    base_weights = {category: 0.04 for category in CATEGORY_AMOUNT_RANGES if category not in {"transfer", "cash_withdrawal"}}
    base_weights.update(account["favorite_categories"])

    if is_fraud:
        for category, factor in {"travel": 2.4, "shopping": 2.2, "health": 1.5}.items():
            base_weights[category] = base_weights.get(category, 0.05) * factor

    return choose_weighted(base_weights, rng)


def _pick_transaction_type(category: str, is_fraud: bool, rng) -> str:
    if category == "utilities":
        return "bill_payment"
    if category == "transport" and rng.random() < 0.18:
        return "atm_withdrawal"
    if category == "travel" and (is_fraud or rng.random() < 0.45):
        return "online_purchase"
    if rng.random() < 0.17:
        return "pix_out"
    return "card_purchase"


def _pick_location(account: dict[str, Any], is_fraud: bool, rng) -> str:
    home_city = account["home_city"]
    nearby_cities = CITY_NETWORK.get(home_city, [])

    if is_fraud:
        return rng.choice(TRAVEL_CITIES)
    if nearby_cities and rng.random() < 0.12:
        return rng.choice(nearby_cities)
    if rng.random() < 0.03:
        return rng.choice(TRAVEL_CITIES)
    return home_city


def _pick_amount(account: dict[str, Any], category: str, is_fraud: bool, rng) -> float:
    minimum_amount, maximum_amount = CATEGORY_AMOUNT_RANGES[category]
    salary_factor = max(0.8, min(2.3, account["salary"] / 3800.0))
    amount = rng.uniform(minimum_amount, maximum_amount * salary_factor)

    if is_fraud:
        amount *= rng.uniform(2.5, 6.5)
        amount = max(amount, account["salary"] * rng.uniform(0.18, 0.65))

    return round(amount, 2)


def _pick_counterparty(account_id: str, all_account_ids: list[str], rng, incoming: bool = False) -> tuple[str, str]:
    if len(all_account_ids) <= 1:
        other_account = "EXTERNAL_ACCOUNT"
    else:
        other_account = account_id
        while other_account == account_id:
            other_account = rng.choice(all_account_ids)

    if incoming:
        return other_account, account_id
    return account_id, other_account


def _salary_transaction(account: dict[str, Any], current_date, transaction_id: str, rng) -> dict[str, Any]:
    timestamp = datetime.combine(
        current_date,
        time(hour=rng.randint(6, 10), minute=rng.randint(0, 59), second=rng.randint(0, 59)),
    )
    return {
        "transaction_id": transaction_id,
        "account_id": account["account_id"],
        "timestamp": timestamp,
        "transaction_type": "salary_deposit",
        "amount": round(account["salary"], 2),
        "signed_amount": round(account["salary"], 2),
        "merchant_category": "salary",
        "transaction_channel": "bank_transfer",
        "location": account["home_city"],
        "is_fraud": False,
        "origin_account": "EMPLOYER",
        "destination_account": account["account_id"],
    }


def _incoming_transfer(account: dict[str, Any], current_date, transaction_id: str, all_account_ids: list[str], rng) -> dict[str, Any]:
    origin_account, destination_account = _pick_counterparty(
        account["account_id"],
        all_account_ids,
        rng,
        incoming=True,
    )
    amount = round(rng.uniform(35.0, min(account["salary"] * 0.45, 1100.0)), 2)
    timestamp = random_timestamp(current_date, 7, 22, rng)
    return {
        "transaction_id": transaction_id,
        "account_id": account["account_id"],
        "timestamp": timestamp,
        "transaction_type": "pix_in",
        "amount": amount,
        "signed_amount": amount,
        "merchant_category": "transfer",
        "transaction_channel": "pix",
        "location": account["home_city"],
        "is_fraud": False,
        "origin_account": origin_account,
        "destination_account": destination_account,
    }


def _spending_transaction(
    account: dict[str, Any],
    current_date,
    transaction_id: str,
    all_account_ids: list[str],
    is_fraud: bool,
    rng,
) -> dict[str, Any]:
    spending_category = _pick_spending_category(account, is_fraud=is_fraud, rng=rng)
    transaction_type = _pick_transaction_type(spending_category, is_fraud=is_fraud, rng=rng)
    transaction_channel = rng.choice(TYPE_CHANNELS[transaction_type])
    merchant_category = spending_category

    if transaction_type == "pix_out":
        merchant_category = "transfer"
    elif transaction_type == "atm_withdrawal":
        merchant_category = "cash_withdrawal"

    if is_fraud:
        timestamp = random_timestamp(current_date, 0, 4, rng)
        if rng.random() < 0.35:
            timestamp = random_timestamp(current_date, 22, 23, rng)
    else:
        timestamp = random_timestamp(
            current_date,
            account["active_hour_start"],
            account["active_hour_end"],
            rng,
        )

    amount = _pick_amount(account, category=merchant_category, is_fraud=is_fraud, rng=rng)
    location = _pick_location(account, is_fraud=is_fraud, rng=rng)

    if transaction_type == "pix_out":
        origin_account, destination_account = _pick_counterparty(account["account_id"], all_account_ids, rng)
        location = account["home_city"] if not is_fraud else location
    else:
        origin_account = account["account_id"]
        destination_account = f"MERCHANT_{merchant_category.upper()}"

    if merchant_category == "cash_withdrawal":
        destination_account = "ATM_NETWORK"
        location = account["home_city"] if not is_fraud else rng.choice(TRAVEL_CITIES)

    if transaction_type == "bill_payment":
        destination_account = "UTILITY_PROVIDER"

    return {
        "transaction_id": transaction_id,
        "account_id": account["account_id"],
        "timestamp": timestamp,
        "transaction_type": transaction_type,
        "amount": amount,
        "signed_amount": -amount,
        "merchant_category": merchant_category,
        "transaction_channel": transaction_channel,
        "location": location,
        "is_fraud": bool(is_fraud),
        "origin_account": origin_account,
        "destination_account": destination_account,
    }


def _finalize_candidate(candidate: dict[str, Any], current_balance: float, rng) -> tuple[dict[str, Any] | None, float]:
    signed_amount = float(candidate.pop("signed_amount"))
    amount = float(candidate["amount"])

    if signed_amount < 0:
        if current_balance <= 20:
            return None, current_balance
        if amount > current_balance:
            amount = round(max(8.0, current_balance * rng.uniform(0.25, 0.95)), 2)
            signed_amount = -amount
            candidate["amount"] = amount

    balance_before = round(current_balance, 2)
    balance_after = round(balance_before + signed_amount, 2)
    candidate["balance_before"] = balance_before
    candidate["balance_after"] = balance_after
    candidate["timestamp"] = candidate["timestamp"].isoformat()
    candidate["is_fraud"] = int(candidate["is_fraud"])
    return candidate, balance_after


def generate_transactions(
    accounts: list[dict[str, Any]] | pd.DataFrame,
    config: GenerationConfig,
) -> list[dict[str, Any]]:
    config.validate()
    rng = build_rng(config.seed)
    account_records = _coerce_accounts(accounts)
    all_account_ids = [account["account_id"] for account in account_records]
    start_date, end_date = config.resolve_dates()

    transactions: list[dict[str, Any]] = []
    transaction_number = 1

    for account in account_records:
        current_balance = float(account["current_balance"])

        for current_date in date_sequence(start_date, end_date):
            daily_candidates: list[dict[str, Any]] = []

            if current_date.day == account["salary_day"]:
                transaction_id = f"TX{transaction_number:09d}"
                transaction_number += 1
                daily_candidates.append(_salary_transaction(account, current_date, transaction_id, rng))

            if rng.random() < 0.06:
                transaction_id = f"TX{transaction_number:09d}"
                transaction_number += 1
                daily_candidates.append(
                    _incoming_transfer(account, current_date, transaction_id, all_account_ids, rng),
                )

            daily_target = _daily_transactions_target(account, current_date, rng)
            anomaly_budget = 1 if rng.random() < config.fraud_rate else 0

            for _ in range(daily_target):
                is_fraud = anomaly_budget > 0 and rng.random() < 0.55
                transaction_id = f"TX{transaction_number:09d}"
                transaction_number += 1
                daily_candidates.append(
                    _spending_transaction(
                        account,
                        current_date,
                        transaction_id,
                        all_account_ids,
                        is_fraud=is_fraud,
                        rng=rng,
                    ),
                )
                if is_fraud:
                    anomaly_budget -= 1

            daily_candidates.sort(key=lambda item: item["timestamp"])

            for candidate in daily_candidates:
                finalized_candidate, current_balance = _finalize_candidate(candidate, current_balance, rng)
                if finalized_candidate is not None:
                    transactions.append(finalized_candidate)

        account["current_balance"] = round(current_balance, 2)

    return transactions


def transactions_to_frame(transactions: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(transactions)
    if frame.empty:
        return frame
    return frame.sort_values(["account_id", "timestamp", "transaction_id"]).reset_index(drop=True)


def validate_transactions(transactions: list[dict[str, Any]] | pd.DataFrame) -> None:
    transactions_frame = transactions.copy() if isinstance(transactions, pd.DataFrame) else transactions_to_frame(transactions)
    if transactions_frame.empty:
        msg = "O dataset de transacoes gerado esta vazio."
        raise ValueError(msg)
    if transactions_frame["transaction_id"].duplicated().any():
        msg = "Foram encontrados transaction_id duplicados no dataset de transacoes."
        raise ValueError(msg)
    if transactions_frame.isna().sum().sum() > 0:
        msg = "Foram encontrados valores nulos no dataset de transacoes."
        raise ValueError(msg)
    if (transactions_frame["amount"] <= 0).any():
        msg = "Foram encontrados valores monetarios nao positivos no dataset de transacoes."
        raise ValueError(msg)
    if (transactions_frame["balance_after"] < 0).any():
        msg = "Foram encontrados saldos finais negativos no dataset de transacoes."
        raise ValueError(msg)

    continuity_errors = 0
    ordered_transactions = transactions_frame.sort_values(["account_id", "timestamp", "transaction_id"])
    for _, account_group in ordered_transactions.groupby("account_id", sort=False):
        previous_balance_after = None
        for row in account_group.itertuples(index=False):
            if previous_balance_after is not None and round(float(row.balance_before), 2) != round(float(previous_balance_after), 2):
                continuity_errors += 1
            previous_balance_after = row.balance_after

    if continuity_errors:
        msg = "Foram encontrados erros de continuidade de saldo entre transacoes sequenciais."
        raise ValueError(msg)


def save_transactions(transactions: list[dict[str, Any]], output_path: Path | None = None) -> Path:
    resolved_path = output_path or DEFAULT_TRANSACTIONS_PATH
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    transactions_to_frame(transactions).to_csv(resolved_path, index=False)
    return resolved_path
