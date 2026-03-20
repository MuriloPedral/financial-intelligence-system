# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# ast ajuda a interpretar estruturas serializadas em string, caso os perfis venham de um CSV.
import ast

# Pandas organiza a tabela final de recomendacoes.
import pandas as pd

# Importa a traducao das categorias para montar textos em portugues.
from src.utils.labels import humanize_category


# Categorias mais associadas a consumo impulsivo no contexto deste projeto.
IMPULSIVE_CATEGORIES = {"restaurant", "entertainment", "shopping"}


def _coerce_mapping(value: object) -> dict[str, float]:
    # Valores ausentes viram dicionario vazio.
    if value is None:
        return {}
    # Se ja vier como dicionario, apenas normaliza os tipos.
    if isinstance(value, dict):
        return {str(key): float(item) for key, item in value.items()}
    # Se vier como texto, tenta reconstruir a estrutura.
    if isinstance(value, str) and value.strip():
        parsed_value = ast.literal_eval(value)
        if isinstance(parsed_value, dict):
            return {str(key): float(item) for key, item in parsed_value.items()}
    # Fallback seguro.
    return {}


def _build_single_account_recommendation(profile: dict[str, object]) -> dict[str, object]:
    # Normaliza as distribuicoes vindas do perfil para uso local.
    spending_distribution = _coerce_mapping(profile.get("spending_category_amount_share"))

    # Ordena as categorias pela participacao no gasto.
    sorted_categories = sorted(
        spending_distribution.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    # Extrai os principais indicadores do perfil financeiro.
    top_category = sorted_categories[0][0] if sorted_categories else "unknown"
    top_category_share = float(sorted_categories[0][1]) if sorted_categories else 0.0
    top_two_share = sum(share for _, share in sorted_categories[:2])
    category_diversity = int(profile.get("category_diversity", 0))
    impulsive_spending_share = float(profile.get("impulsive_spending_share", 0.0))
    estimated_monthly_income = float(profile.get("estimated_monthly_income", 0.0))
    average_monthly_spend = float(profile.get("average_monthly_spend", 0.0))
    spend_to_income_ratio = float(profile.get("spend_to_income_ratio", 0.0))
    cash_withdrawal_share = float(spending_distribution.get("cash_withdrawal", 0.0))

    # Aqui serao acumuladas as mensagens personalizadas para a conta.
    recommendations: list[str] = []

    # Aponta quando uma unica categoria domina o orcamento.
    if top_category_share >= 0.40:
        category_label = humanize_category(top_category).lower()
        recommendations.append(
            f"Voce esta destinando {top_category_share:.0%} dos seus gastos para {category_label}. Considere revisar essa categoria.",
        )

    # Aponta quando os gastos estao excessivamente concentrados.
    if category_diversity <= 2 or top_two_share >= 0.75:
        recommendations.append(
            "Seu padrao de gastos esta concentrado em poucas categorias. Diversificar melhor o orcamento pode reduzir riscos.",
        )

    # Marca quando despesas mais impulsivas pesam demais.
    if impulsive_spending_share >= 0.35:
        recommendations.append(
            f"Restaurante, entretenimento e compras representam {impulsive_spending_share:.0%} dos seus gastos. Vale acompanhar possiveis despesas impulsivas.",
        )

    # Compara o gasto mensal medio com a renda estimada da conta.
    if estimated_monthly_income > 0:
        if spend_to_income_ratio >= 1.0:
            recommendations.append(
                f"Seu gasto mensal estimado esta em {spend_to_income_ratio:.0%} da renda estimada. Isso indica consumo acima da capacidade observada.",
            )
        elif spend_to_income_ratio >= 0.85:
            recommendations.append(
                f"Seu consumo mensal medio ja compromete {spend_to_income_ratio:.0%} da renda estimada. Considere criar uma margem maior de folga.",
            )

    # Saques recorrentes tambem podem indicar baixa visibilidade do controle financeiro.
    if cash_withdrawal_share >= 0.15:
        recommendations.append(
            f"Saques em dinheiro representam {cash_withdrawal_share:.0%} dos seus gastos. Monitorar melhor esse fluxo pode ajudar no controle financeiro.",
        )

    # Guarda quantas recomendacoes realmente pedem atencao do usuario.
    actionable_recommendations = len(recommendations)

    # Garante ao menos um feedback util quando o perfil parece equilibrado.
    if not recommendations:
        recommendations.append(
            "Seu padrao financeiro parece equilibrado no periodo analisado. Continue acompanhando as categorias com maior peso no orcamento.",
        )

    # Calcula uma prioridade simples para ordenar as contas no terminal e no relatorio.
    recommendation_priority = round(
        actionable_recommendations * 2
        + max(0.0, top_category_share - 0.40) * 4
        + max(0.0, impulsive_spending_share - 0.35) * 3
        + min(3.0, max(0.0, spend_to_income_ratio - 0.85) * 1.5),
        4,
    )

    # Retorna a linha final pronta para virar DataFrame.
    return {
        "account_id": str(profile["account_id"]),
        "top_spending_category": top_category,
        "top_spending_share": round(top_category_share, 4),
        "estimated_monthly_income": round(estimated_monthly_income, 2),
        "average_monthly_spend": round(average_monthly_spend, 2),
        "spend_to_income_ratio": round(spend_to_income_ratio, 4),
        "impulsive_spending_share": round(impulsive_spending_share, 4),
        "recommendations": recommendations,
        "recommendations_text": " | ".join(recommendations),
        "recommendation_count": len(recommendations),
        "actionable_recommendation_count": actionable_recommendations,
        "has_actionable_recommendation": int(actionable_recommendations > 0),
        "recommendation_priority": recommendation_priority,
    }


def build_financial_recommendations(account_profiles: pd.DataFrame) -> pd.DataFrame:
    # Sem perfis financeiros nao ha recomendacoes para construir.
    if account_profiles.empty:
        return pd.DataFrame()

    # Gera uma recomendacao por conta.
    recommendation_rows = [
        _build_single_account_recommendation(profile)
        for profile in account_profiles.to_dict(orient="records")
    ]

    # Devolve uma tabela ordenada para facilitar leitura e exportacao.
    return pd.DataFrame(recommendation_rows).sort_values(
        ["recommendation_priority", "account_id"],
        ascending=[False, True],
    ).reset_index(drop=True)
