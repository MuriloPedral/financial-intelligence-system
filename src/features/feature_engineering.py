# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Numpy ajuda nos calculos numericos e no tratamento de infinitos.
import numpy as np
# Pandas manipula as tabelas de transacoes.
import pandas as pd


def engineer_transaction_features(transactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Copia e ordena as transacoes para preservar a ordem cronologica por conta.
    enriched_transactions = transactions.copy().sort_values(["account_id", "timestamp"]).reset_index(drop=True)
    # Cria um agrupamento por conta para calcular estatisticas comportamentais.
    grouped = enriched_transactions.groupby("account_id", sort=False)

    # Extrai a hora da transacao.
    enriched_transactions["hour"] = enriched_transactions["timestamp"].dt.hour
    # Extrai o dia da semana.
    enriched_transactions["day_of_week"] = enriched_transactions["timestamp"].dt.dayofweek
    # Extrai o dia do mes.
    enriched_transactions["day_of_month"] = enriched_transactions["timestamp"].dt.day
    # Marca se a transacao ocorreu no fim de semana.
    enriched_transactions["is_weekend"] = (enriched_transactions["day_of_week"] >= 5).astype(int)
    # Aplica log para suavizar diferencas grandes de valor.
    enriched_transactions["amount_log"] = np.log1p(enriched_transactions["amount"])
    # Mede a variacao bruta do saldo causada pela transacao.
    enriched_transactions["balance_change"] = (
        enriched_transactions["balance_after"] - enriched_transactions["balance_before"]
    )
    # Mede a variacao do saldo proporcionalmente ao saldo anterior.
    enriched_transactions["balance_delta_ratio"] = (
        enriched_transactions["balance_change"]
        / enriched_transactions["balance_before"].replace(0, np.nan)
    )
    # Mede o peso da transacao em relacao ao saldo anterior.
    enriched_transactions["amount_to_balance_ratio"] = (
        enriched_transactions["amount"]
        / enriched_transactions["balance_before"].replace(0, np.nan)
    )
    # Conta quantas transacoes aquela conta possui no dataset.
    enriched_transactions["account_transaction_count"] = grouped["transaction_id"].transform("count")
    # Calcula o valor medio movimentado pela conta.
    enriched_transactions["account_mean_amount"] = grouped["amount"].transform("mean")
    # Calcula o desvio padrao dos valores daquela conta.
    enriched_transactions["account_std_amount"] = grouped["amount"].transform("std").fillna(0.0)
    # Calcula a mediana de valores por conta.
    enriched_transactions["account_median_amount"] = grouped["amount"].transform("median")
    # Guarda o maior valor observado por conta.
    enriched_transactions["account_max_amount"] = grouped["amount"].transform("max")
    # Calcula o percentil 90 dos valores da conta para detectar exageros.
    enriched_transactions["account_amount_p90"] = grouped["amount"].transform(lambda values: values.quantile(0.90))
    # Compara o valor atual com a media da conta.
    enriched_transactions["amount_vs_account_mean"] = (
        enriched_transactions["amount"]
        / enriched_transactions["account_mean_amount"].replace(0, np.nan)
    )
    # Compara o valor atual com o percentil 90 da conta.
    enriched_transactions["amount_vs_account_p90"] = (
        enriched_transactions["amount"]
        / enriched_transactions["account_amount_p90"].replace(0, np.nan)
    )
    # Mede o intervalo de tempo desde a transacao anterior da mesma conta.
    enriched_transactions["transaction_gap_minutes"] = (
        grouped["timestamp"].diff().dt.total_seconds().div(60).fillna(0.0)
    )
    # Marca transacoes de madrugada ou muito tarde da noite.
    enriched_transactions["is_night_transaction"] = (
        (enriched_transactions["hour"] <= 5) | (enriched_transactions["hour"] >= 23)
    ).astype(int)

    # Usa a moda da localizacao como uma aproximacao da localizacao habitual da conta.
    home_location = grouped["location"].transform(
        lambda values: values.mode().iat[0] if not values.mode().empty else values.iloc[0],
    )
    # Usa a mediana do horario para representar o horario mais comum da conta.
    median_active_hour = grouped["hour"].transform("median")

    # Salva a localizacao habitual aproximada.
    enriched_transactions["home_location_proxy"] = home_location
    # Marca quando a transacao aconteceu fora do padrao geografico observado.
    enriched_transactions["is_unusual_location"] = (
        enriched_transactions["location"] != enriched_transactions["home_location_proxy"]
    ).astype(int)
    # Mede o quanto a hora atual se distancia do horario mediano da conta.
    enriched_transactions["distance_from_usual_hour"] = (
        enriched_transactions["hour"] - median_active_hour
    ).abs()
    # Marca valores acima do percentil 90 da propria conta.
    enriched_transactions["is_large_transaction"] = (
        enriched_transactions["amount"] > enriched_transactions["account_amount_p90"]
    ).astype(int)

    # Lista as colunas que entrarao no modelo de machine learning.
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

    # Converte colunas categoricas em colunas binarias numericas.
    feature_matrix = pd.get_dummies(
        enriched_transactions[feature_columns],
        columns=["transaction_type", "merchant_category", "transaction_channel", "location"],
        dtype=float,
    )

    # Troca infinitos por nulos e depois preenche tudo com zero.
    feature_matrix = feature_matrix.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    # Retorna tanto o dataset enriquecido quanto a matriz pronta para o modelo.
    return enriched_transactions, feature_matrix
