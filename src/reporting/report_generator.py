# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# json ajuda a serializar listas e dicionarios antes de salvar CSV.
import json
# Path e usado para montar o caminho do relatorio final.
from pathlib import Path

# Pandas representa e manipula o dataset de saida.
import pandas as pd

# Importa o caminho padrao do relatorio para reaproveitar a configuracao central.
from src.config import DEFAULT_PROFILE_REPORT_PATH, DEFAULT_RECOMMENDATIONS_PATH, DEFAULT_REPORT_PATH


def build_summary(
    scored_transactions: pd.DataFrame,
    account_profiles: pd.DataFrame | None = None,
    recommendations: pd.DataFrame | None = None,
) -> dict[str, int]:
    # Resume o volume total analisado para mostrar no terminal.
    summary = {
        "total_transactions": int(len(scored_transactions)),
        "total_accounts": int(scored_transactions["account_id"].nunique()),
        "anomalies_detected": int(scored_transactions["is_anomaly"].sum()),
    }

    # Quando o dataset possui rotulo de fraude, calcula metricas adicionais.
    if "is_fraud" in scored_transactions.columns:
        summary["labeled_frauds"] = int(scored_transactions["is_fraud"].sum())
        summary["labeled_frauds_flagged"] = int(
            scored_transactions.loc[scored_transactions["is_anomaly"] == 1, "is_fraud"].sum(),
        )

    # Quando o pipeline gera explicacoes, resume essa nova camada de inteligencia.
    if "explanation_count" in scored_transactions.columns:
        summary["anomalies_explained"] = int(
            scored_transactions.loc[scored_transactions["is_anomaly"] == 1, "explanation_count"].gt(0).sum(),
        )

    # Resume a camada de perfis financeiros por conta.
    if account_profiles is not None and not account_profiles.empty:
        summary["profiles_generated"] = int(len(account_profiles))

    # Resume a camada de recomendacoes personalizadas por conta.
    if recommendations is not None and not recommendations.empty:
        actionable_column = "has_actionable_recommendation"
        if actionable_column in recommendations.columns:
            summary["accounts_with_recommendations"] = int(recommendations[actionable_column].sum())
        else:
            summary["accounts_with_recommendations"] = int(recommendations["recommendation_count"].gt(0).sum())
        summary["total_recommendations"] = int(recommendations["recommendation_count"].sum())

    # Devolve um dicionario simples para ser reutilizado em outros formatos de saida.
    return summary


def select_top_anomalies(scored_transactions: pd.DataFrame, top_n: int) -> pd.DataFrame:
    # Filtra apenas as transacoes marcadas como anomalia.
    top_anomalies = scored_transactions.loc[scored_transactions["is_anomaly"] == 1].copy()
    # Ordena por score para colocar os casos mais extremos primeiro.
    top_anomalies = top_anomalies.sort_values(
        ["anomaly_score", "raw_anomaly_score", "timestamp"],
        ascending=[False, False, False],
    )
    # Limita a quantidade de linhas exibidas no ranking.
    return top_anomalies.head(top_n)


def save_anomaly_report(scored_transactions: pd.DataFrame, output_path: str | Path | None = None) -> Path:
    # Usa o caminho informado pelo usuario ou o caminho padrao do projeto.
    resolved_path = Path(output_path) if output_path else DEFAULT_REPORT_PATH
    # Garante que a pasta de destino exista.
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    # Salva o CSV ordenado para facilitar leitura posterior.
    report_frame = scored_transactions.sort_values(
        ["is_anomaly", "anomaly_score", "timestamp"],
        ascending=[False, False, False],
    )
    _serialize_for_export(report_frame).to_csv(resolved_path, index=False)
    # Retorna o caminho final salvo.
    return resolved_path


def _serialize_for_export(dataset: pd.DataFrame) -> pd.DataFrame:
    # Copia o DataFrame para evitar alterar estruturas em memoria usadas por outros modulos.
    export_frame = dataset.copy()

    # Serializa listas e dicionarios em JSON para preservar a estrutura nos CSVs.
    for column in export_frame.columns:
        export_frame[column] = export_frame[column].apply(
            lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True)
            if isinstance(value, (list, dict))
            else value,
        )

    # Retorna a versao pronta para exportacao.
    return export_frame


def save_account_profiles(account_profiles: pd.DataFrame, output_path: str | Path | None = None) -> Path:
    # Usa o caminho informado pelo usuario ou o caminho padrao do projeto.
    resolved_path = Path(output_path) if output_path else DEFAULT_PROFILE_REPORT_PATH
    # Garante que a pasta de destino exista.
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    # Salva o CSV com serializacao amigavel das estruturas mais complexas.
    _serialize_for_export(account_profiles).to_csv(resolved_path, index=False)
    return resolved_path


def save_financial_recommendations(
    recommendations: pd.DataFrame,
    output_path: str | Path | None = None,
) -> Path:
    # Usa o caminho informado pelo usuario ou o caminho padrao do projeto.
    resolved_path = Path(output_path) if output_path else DEFAULT_RECOMMENDATIONS_PATH
    # Garante que a pasta de destino exista.
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    # Salva o CSV com serializacao amigavel das estruturas mais complexas.
    _serialize_for_export(recommendations).to_csv(resolved_path, index=False)
    return resolved_path


def select_featured_recommendations(recommendations: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    # Sem recomendacoes, devolve um DataFrame vazio.
    if recommendations.empty:
        return recommendations.copy()

    # Prioriza contas com recomendacoes realmente acionaveis.
    if "has_actionable_recommendation" in recommendations.columns:
        actionable_recommendations = recommendations.loc[recommendations["has_actionable_recommendation"] == 1]
        if not actionable_recommendations.empty:
            recommendations = actionable_recommendations

    # Ordena pelas contas com maior prioridade analitica.
    featured_recommendations = recommendations.sort_values(
        ["recommendation_priority", "recommendation_count", "spend_to_income_ratio", "account_id"],
        ascending=[False, False, False, True],
    )

    # Limita a quantidade de contas exibidas no terminal.
    return featured_recommendations.head(top_n).reset_index(drop=True)


def format_generation_report(summary: dict[str, object]) -> str:
    # Monta uma saida de terminal mais legivel para a fase de geracao.
    lines = [
        "=" * 72,
        "GERACAO DE DADOS SINTETICOS CONCLUIDA",
        "=" * 72,
        "",
        "Resumo da simulacao:",
        f"- Periodo simulado: {summary['start_date']} ate {summary['end_date']}",
        f"- Contas geradas: {summary['accounts_count']}",
        f"- Transacoes geradas: {summary['transactions_count']}",
        f"- Transacoes marcadas como fraude: {summary['fraud_transactions']}",
        f"- Taxa de fraude configurada: {summary['fraud_rate']:.2%}",
        "",
        "Arquivos gerados:",
        f"- Contas: {summary['accounts_path']}",
        f"- Transacoes: {summary['transactions_path']}",
        "",
        "Proximo passo sugerido:",
        "- Rode: python main.py",
    ]
    # Concatena tudo com quebra de linha para imprimir em bloco.
    return "\n".join(lines)


def format_console_report(
    dataset_path: Path,
    report_path: Path,
    profiles_path: Path,
    recommendations_path: Path,
    summary: dict[str, int],
    top_anomalies: pd.DataFrame,
    featured_recommendations: pd.DataFrame,
) -> str:
    # Monta o cabecalho principal do relatorio de inteligencia financeira.
    lines = [
        "=" * 72,
        "RELATORIO DE INTELIGENCIA FINANCEIRA",
        "=" * 72,
        "",
        "Resumo da execucao:",
        f"- Dataset analisado: {dataset_path}",
        f"- Transacoes analisadas: {summary['total_transactions']}",
        f"- Contas analisadas: {summary['total_accounts']}",
        f"- Perfis financeiros gerados: {summary.get('profiles_generated', summary['total_accounts'])}",
        f"- Anomalias detectadas: {summary['anomalies_detected']}",
    ]

    # Resume o volume de anomalias que receberam explicacao legivel.
    if "anomalies_explained" in summary:
        lines.append(f"- Anomalias explicadas: {summary['anomalies_explained']}")

    # Resume o volume de recomendacoes personalizadas geradas por conta.
    if "accounts_with_recommendations" in summary:
        lines.append(f"- Contas com recomendacoes: {summary['accounts_with_recommendations']}")
        lines.append(f"- Total de recomendacoes geradas: {summary['total_recommendations']}")

    # Quando houver rotulo de fraude no dataset, mostra um resumo adicional.
    if "labeled_frauds" in summary:
        lines.append(f"- Fraudes rotuladas no dataset: {summary['labeled_frauds']}")
        lines.append(f"- Fraudes rotuladas detectadas pelo modelo: {summary['labeled_frauds_flagged']}")

    lines.append("")
    lines.append("Arquivos gerados:")
    lines.append(f"- Relatorio de anomalias: {report_path}")
    lines.append(f"- Perfis financeiros: {profiles_path}")
    lines.append(f"- Recomendacoes financeiras: {recommendations_path}")
    lines.append("")
    lines.append("Ranking das transacoes mais suspeitas:")

    # Se nada foi marcado, informa isso claramente no terminal.
    if top_anomalies.empty:
        lines.append("- Nenhuma anomalia foi detectada com a configuracao atual.")
    else:
        # Itera no ranking final para imprimir cada transacao de forma amigavel.
        position = 1
        for row in top_anomalies.itertuples(index=False):
            # So mostra o marcador de fraude quando a coluna existe no dataset.
            fraud_marker = ""
            if hasattr(row, "is_fraud"):
                fraud_marker = f" | fraude_rotulada: {row.is_fraud}"

            # Cada item do ranking vira uma linha clara e compacta.
            lines.append(
                f"{position}. conta: {row.account_id} | valor: {row.amount:.2f} | "
                f"score: {row.anomaly_score:.2f} | tipo: {row.transaction_type} | "
                f"local: {row.location} | data_hora: {row.timestamp}{fraud_marker}",
            )

            # Quando houver explicacao, mostra logo abaixo do item do ranking.
            if hasattr(row, "anomaly_explanation") and row.anomaly_explanation:
                lines.append(f"   explicacao: {row.anomaly_explanation}")

            # Atualiza a numeracao do ranking.
            position += 1

    # Reserva uma secao final para destacar recomendacoes personalizadas.
    lines.append("")
    lines.append("Recomendacoes em destaque:")

    # Se nenhuma recomendacao foi gerada, informa isso claramente.
    if featured_recommendations.empty:
        lines.append("- Nenhuma recomendacao relevante foi gerada para o periodo analisado.")
        return "\n".join(lines)

    # Mostra as contas com recomendacoes mais relevantes.
    for row in featured_recommendations.itertuples(index=False):
        lines.append(f"- Conta {row.account_id}: {row.recommendations_text}")

    # Retorna o bloco final pronto para impressao.
    return "\n".join(lines)
