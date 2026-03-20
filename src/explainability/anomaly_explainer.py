# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# ast ajuda a interpretar estruturas serializadas em string, caso o modulo seja reutilizado depois de um CSV.
import ast

# Pandas organiza as tabelas de entrada e saida.
import pandas as pd

# Importa o lookup de perfis para comparar cada transacao com o historico da conta.
from src.profiles.account_profiles import build_account_profile_lookup
# Importa os tradutores de categorias e tipos para montar textos amigaveis.
from src.utils.labels import humanize_category, humanize_transaction_type


def _coerce_mapping(value: object) -> dict[str, float]:
    # Valores ausentes viram um dicionario vazio por padrao.
    if value is None:
        return {}
    # Se ja vier como dicionario, apenas normaliza as chaves para string.
    if isinstance(value, dict):
        return {str(key): float(item) for key, item in value.items()}
    # Se vier serializado em texto, tenta reconstruir o dicionario.
    if isinstance(value, str) and value.strip():
        parsed_value = ast.literal_eval(value)
        if isinstance(parsed_value, dict):
            return {str(key): float(item) for key, item in parsed_value.items()}
    # Em qualquer outro caso, devolve vazio.
    return {}


def _coerce_list(value: object) -> list[int]:
    # Valores ausentes viram lista vazia por padrao.
    if value is None:
        return []
    # Se ja vier como lista, normaliza os itens para inteiro.
    if isinstance(value, list):
        return [int(item) for item in value]
    # Se vier serializado em texto, tenta reconstruir a lista.
    if isinstance(value, str) and value.strip():
        parsed_value = ast.literal_eval(value)
        if isinstance(parsed_value, list):
            return [int(item) for item in parsed_value]
    # Fallback seguro.
    return []


def _distribution_value(distribution: object, key: object) -> float:
    # Normaliza a estrutura antes de consultar o valor desejado.
    normalized_distribution = _coerce_mapping(distribution)
    # Usa zero quando a chave nao existe.
    return float(normalized_distribution.get(str(key), 0.0))


def _explain_transaction(transaction: dict[str, object], profile: dict[str, object]) -> list[str]:
    # Acumula todos os motivos encontrados para a transacao anomala.
    reasons: list[str] = []

    # Extrai campos numericos necessarios para as heuristicas.
    amount = float(transaction.get("amount", 0.0))
    mean_amount = float(profile.get("mean_amount", 0.0))
    amount_std = float(profile.get("amount_std", 0.0))
    transaction_hour = int(transaction.get("hour", pd.Timestamp(transaction["timestamp"]).hour))
    median_activity_hour = float(profile.get("median_activity_hour", transaction_hour))
    transaction_gap_minutes = float(transaction.get("transaction_gap_minutes", 0.0) or 0.0)
    mean_gap_minutes = float(profile.get("mean_gap_minutes", 0.0) or 0.0)
    amount_to_balance_ratio = float(transaction.get("amount_to_balance_ratio", 0.0) or 0.0)
    mean_ratio = float(profile.get("mean_amount_to_balance_ratio", 0.0) or 0.0)

    # Compara o valor atual com o tamanho medio de transacao daquela conta.
    if mean_amount > 0:
        amount_multiple = amount / mean_amount
        if amount_multiple >= 3:
            reasons.append(f"Valor da transacao {amount_multiple:.1f}x maior que a media da conta.")
        elif amount_std > 0 and amount >= mean_amount + (2.5 * amount_std):
            reasons.append("Valor acima do desvio habitual observado na conta.")

    # Verifica se a transacao aconteceu fora dos horarios mais comuns.
    usual_activity_hours = set(_coerce_list(profile.get("usual_activity_hours")))
    if usual_activity_hours and transaction_hour not in usual_activity_hours and abs(transaction_hour - median_activity_hour) >= 4:
        reasons.append("Transacao realizada em horario incomum para a conta.")

    # Compara a categoria atual com o historico de gastos daquela conta.
    merchant_category = str(transaction.get("merchant_category", "unknown"))
    category_share = _distribution_value(profile.get("spending_category_count_share"), merchant_category)
    is_outflow = float(transaction.get("balance_after", 0.0)) < float(transaction.get("balance_before", 0.0))
    if is_outflow and category_share < 0.12:
        category_label = humanize_category(merchant_category).lower()
        reasons.append(f"Categoria {category_label} raramente utilizada por esta conta.")

    # Verifica se o tipo operacional aparece pouco no historico.
    transaction_type = str(transaction.get("transaction_type", "unknown"))
    type_share = _distribution_value(profile.get("transaction_type_distribution"), transaction_type)
    if type_share < 0.12:
        transaction_type_label = humanize_transaction_type(transaction_type).lower()
        reasons.append(f"Tipo {transaction_type_label} pouco frequente no historico da conta.")

    # Compara a localizacao atual com os locais mais comuns da conta.
    location = str(transaction.get("location", "unknown"))
    location_share = _distribution_value(profile.get("location_distribution"), location)
    home_location = str(profile.get("home_location", "unknown"))
    if home_location and location != home_location and location_share < 0.18:
        reasons.append("Localizacao incomum em relacao ao historico da conta.")

    # Mede se as transacoes ficaram muito proximas entre si em relacao ao padrao recente.
    if transaction_gap_minutes > 0 and mean_gap_minutes > 0 and transaction_gap_minutes < max(5.0, mean_gap_minutes * 0.35):
        reasons.append("Frequencia de transacoes acima do padrao recente da conta.")

    # Verifica se o valor comprometeu uma parcela muito grande do saldo.
    if amount_to_balance_ratio > 0 and mean_ratio > 0 and amount_to_balance_ratio > max(0.6, mean_ratio * 2.5):
        reasons.append("Valor alto em relacao ao saldo disponivel antes da transacao.")

    # Garante pelo menos uma explicacao legivel mesmo quando nenhuma regra especifica dispara.
    if not reasons:
        reasons.append("Combinacao incomum de valor, horario e contexto em relacao ao perfil historico da conta.")

    # Remove duplicatas preservando a ordem original.
    return list(dict.fromkeys(reasons))


def explain_anomalies(
    scored_transactions: pd.DataFrame,
    account_profiles: pd.DataFrame,
) -> pd.DataFrame:
    # Copia o DataFrame para nao alterar a referencia original fora da funcao.
    explained_transactions = scored_transactions.copy()

    # Monta o lookup de perfis para consulta rapida por account_id.
    profile_lookup = build_account_profile_lookup(account_profiles)

    # Acumula as estruturas de explicacao para cada linha.
    anomaly_reasons: list[list[str]] = []
    anomaly_explanations: list[str] = []
    explanation_counts: list[int] = []

    # Percorre cada transacao e gera explicacao apenas quando ela foi marcada como anomalia.
    for transaction in explained_transactions.to_dict(orient="records"):
        if int(transaction.get("is_anomaly", 0)) != 1:
            anomaly_reasons.append([])
            anomaly_explanations.append("")
            explanation_counts.append(0)
            continue

        # Recupera o perfil da conta correspondente.
        profile = profile_lookup.get(str(transaction["account_id"]), {})
        reasons = _explain_transaction(transaction, profile)

        # Salva a versao estruturada e a versao textual.
        anomaly_reasons.append(reasons)
        anomaly_explanations.append("; ".join(reasons))
        explanation_counts.append(len(reasons))

    # Anexa as novas colunas explicativas no dataset final.
    explained_transactions["anomaly_reasons"] = anomaly_reasons
    explained_transactions["anomaly_explanation"] = anomaly_explanations
    explained_transactions["explanation_count"] = explanation_counts
    return explained_transactions
