from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import DEFAULT_TRANSACTIONS_PATH


REQUIRED_TRANSACTION_COLUMNS = {
    "transaction_id",
    "account_id",
    "timestamp",
    "transaction_type",
    "amount",
    "balance_before",
    "balance_after",
    "merchant_category",
    "transaction_channel",
    "location",
    "origin_account",
    "destination_account",
}


def resolve_dataset_path() -> Path:
    if DEFAULT_TRANSACTIONS_PATH.exists():
        return DEFAULT_TRANSACTIONS_PATH

    msg = "Nenhum dataset sintetico foi encontrado. Gere os dados com 'python run_generation.py' antes de rodar a analise."
    raise FileNotFoundError(msg)


def validate_transaction_dataset(dataset: pd.DataFrame) -> None:
    missing_columns = REQUIRED_TRANSACTION_COLUMNS.difference(dataset.columns)
    if missing_columns:
        formatted_columns = ", ".join(sorted(missing_columns))
        msg = f"O dataset nao possui as colunas obrigatorias: {formatted_columns}"
        raise ValueError(msg)
    if dataset.empty:
        msg = "O dataset esta vazio."
        raise ValueError(msg)
    if dataset["transaction_id"].duplicated().any():
        msg = "O dataset contem transaction_id duplicado."
        raise ValueError(msg)


def load_transaction_dataset() -> tuple[pd.DataFrame, Path]:
    dataset_path = resolve_dataset_path()
    dataset = pd.read_csv(dataset_path)
    validate_transaction_dataset(dataset)

    prepared_dataset = dataset.copy()
    prepared_dataset["timestamp"] = pd.to_datetime(prepared_dataset["timestamp"], errors="coerce")
    prepared_dataset = prepared_dataset.dropna(subset=["timestamp"]).reset_index(drop=True)

    numeric_columns = ["amount", "balance_before", "balance_after"]
    if "is_fraud" in prepared_dataset.columns:
        numeric_columns.append("is_fraud")

    for column in numeric_columns:
        prepared_dataset[column] = pd.to_numeric(prepared_dataset[column], errors="coerce")

    prepared_dataset = prepared_dataset.dropna(subset=["amount", "balance_before", "balance_after"])

    if "is_fraud" in prepared_dataset.columns:
        prepared_dataset["is_fraud"] = prepared_dataset["is_fraud"].fillna(0).astype(int)

    string_columns = [
        "transaction_id",
        "account_id",
        "transaction_type",
        "merchant_category",
        "transaction_channel",
        "location",
        "origin_account",
        "destination_account",
    ]
    for column in string_columns:
        prepared_dataset[column] = prepared_dataset[column].fillna("unknown").astype(str)

    prepared_dataset = prepared_dataset.sort_values(["account_id", "timestamp"]).reset_index(drop=True)
    return prepared_dataset, dataset_path
