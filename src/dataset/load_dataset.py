# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Path representa caminhos de arquivos de forma segura.
from pathlib import Path

# Pandas le e trata o CSV de transacoes.
import pandas as pd

# Importa o caminho padrao das transacoes sinteticas.
from src.config import DEFAULT_TRANSACTIONS_PATH


# Lista de colunas minimas que o pipeline precisa para funcionar.
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
    # O pipeline atual trabalha apenas com o dataset sintetico gerado internamente.
    if DEFAULT_TRANSACTIONS_PATH.exists():
        return DEFAULT_TRANSACTIONS_PATH

    # Se nada for encontrado, informa como resolver.
    msg = "Nenhum dataset sintetico foi encontrado. Gere os dados com 'python run_generation.py' antes de rodar a analise."
    raise FileNotFoundError(msg)


def validate_transaction_dataset(dataset: pd.DataFrame) -> None:
    # Verifica se todas as colunas obrigatorias estao presentes.
    missing_columns = REQUIRED_TRANSACTION_COLUMNS.difference(dataset.columns)
    if missing_columns:
        formatted_columns = ", ".join(sorted(missing_columns))
        msg = f"O dataset nao possui as colunas obrigatorias: {formatted_columns}"
        raise ValueError(msg)
    # Nao faz sentido analisar um dataset vazio.
    if dataset.empty:
        msg = "O dataset esta vazio."
        raise ValueError(msg)
    # O identificador de transacao precisa ser unico para manter rastreabilidade.
    if dataset["transaction_id"].duplicated().any():
        msg = "O dataset contem transaction_id duplicado."
        raise ValueError(msg)


def load_transaction_dataset() -> tuple[pd.DataFrame, Path]:
    # Resolve qual arquivo sera usado na execucao.
    dataset_path = resolve_dataset_path()
    # Le o CSV bruto do disco.
    dataset = pd.read_csv(dataset_path)
    # Valida a estrutura minima antes de continuar.
    validate_transaction_dataset(dataset)

    # Cria uma copia para nao alterar o DataFrame original em memoria.
    prepared_dataset = dataset.copy()
    # Converte a coluna de tempo para datetime.
    prepared_dataset["timestamp"] = pd.to_datetime(prepared_dataset["timestamp"], errors="coerce")
    # Remove linhas cujo timestamp nao pode ser interpretado.
    prepared_dataset = prepared_dataset.dropna(subset=["timestamp"]).reset_index(drop=True)

    # Define quais colunas devem ser numericas.
    numeric_columns = ["amount", "balance_before", "balance_after"]
    # Inclui o rotulo de fraude quando ele existe.
    if "is_fraud" in prepared_dataset.columns:
        numeric_columns.append("is_fraud")

    # Tenta converter essas colunas para numero.
    for column in numeric_columns:
        prepared_dataset[column] = pd.to_numeric(prepared_dataset[column], errors="coerce")

    # Remove linhas que ficaram sem os valores numericos essenciais.
    prepared_dataset = prepared_dataset.dropna(subset=["amount", "balance_before", "balance_after"])

    # Preenche o rotulo de fraude ausente com zero e o converte para inteiro.
    if "is_fraud" in prepared_dataset.columns:
        prepared_dataset["is_fraud"] = prepared_dataset["is_fraud"].fillna(0).astype(int)

    # Define as colunas textuais do dataset.
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
    # Garante que essas colunas nunca fiquem nulas e sempre virem texto.
    for column in string_columns:
        prepared_dataset[column] = prepared_dataset[column].fillna("unknown").astype(str)

    # Ordena por conta e tempo para preservar a sequencia cronologica.
    prepared_dataset = prepared_dataset.sort_values(["account_id", "timestamp"]).reset_index(drop=True)
    # Retorna tanto o DataFrame tratado quanto o caminho usado.
    return prepared_dataset, dataset_path
