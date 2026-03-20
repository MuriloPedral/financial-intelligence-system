from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import DEFAULT_PROFILE_REPORT_PATH, DEFAULT_RECOMMENDATIONS_PATH, DEFAULT_REPORT_PATH


ANOMALY_REPORT_COLUMNS = [
    "anomaly_rank",
    "transaction_id",
    "account_id",
    "timestamp",
    "transaction_type",
    "merchant_category",
    "transaction_channel",
    "location",
    "amount",
    "balance_before",
    "balance_after",
    "anomaly_score",
    "raw_anomaly_score",
    "is_fraud",
    "anomaly_explanation",
    "explanation_count",
]

PROFILE_REPORT_COLUMNS = [
    "account_id",
    "analysis_start",
    "analysis_end",
    "period_days",
    "transaction_count",
    "active_days",
    "active_weeks",
    "mean_amount",
    "amount_std",
    "median_amount",
    "avg_daily_transactions",
    "avg_weekly_transactions",
    "estimated_monthly_income",
    "average_monthly_spend",
    "spend_to_income_ratio",
    "impulsive_spending_share",
    "most_common_transaction_type",
    "most_common_spending_category",
    "category_diversity",
    "usual_activity_hours",
    "median_activity_hour",
    "home_location",
    "mean_gap_minutes",
    "gap_std_minutes",
    "mean_amount_to_balance_ratio",
    "std_amount_to_balance_ratio",
    "transaction_type_distribution",
    "spending_category_amount_share",
    "spending_category_count_share",
    "hour_distribution",
    "location_distribution",
]

RECOMMENDATION_REPORT_COLUMNS = [
    "recommendation_rank",
    "account_id",
    "top_spending_category",
    "top_spending_share",
    "estimated_monthly_income",
    "average_monthly_spend",
    "spend_to_income_ratio",
    "impulsive_spending_share",
    "actionable_recommendation_count",
    "recommendation_priority",
    "recommendations_text",
]


def _serialize_for_export(dataset: pd.DataFrame) -> pd.DataFrame:
    export_frame = dataset.copy()
    for column in export_frame.columns:
        export_frame[column] = export_frame[column].apply(
            lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True)
            if isinstance(value, (list, dict))
            else value,
        )
    return export_frame


def _reindex_columns(dataset: pd.DataFrame, preferred_columns: list[str], keep_extra: bool = False) -> pd.DataFrame:
    existing_preferred_columns = [column for column in preferred_columns if column in dataset.columns]

    if keep_extra:
        ordered_columns = existing_preferred_columns + [
            column for column in dataset.columns if column not in existing_preferred_columns
        ]
        return dataset.reindex(columns=ordered_columns)

    return dataset.loc[:, existing_preferred_columns]


def build_anomaly_report_frame(scored_transactions: pd.DataFrame) -> pd.DataFrame:
    anomaly_report = scored_transactions.loc[scored_transactions["is_anomaly"] == 1].copy()
    if anomaly_report.empty:
        return anomaly_report

    anomaly_report = anomaly_report.sort_values(
        ["anomaly_score", "raw_anomaly_score", "timestamp"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    anomaly_report.insert(0, "anomaly_rank", range(1, len(anomaly_report) + 1))
    return _reindex_columns(anomaly_report, ANOMALY_REPORT_COLUMNS)


def build_account_profiles_report_frame(account_profiles: pd.DataFrame) -> pd.DataFrame:
    if account_profiles.empty:
        return account_profiles.copy()

    ordered_profiles = account_profiles.sort_values("account_id").reset_index(drop=True)
    return _reindex_columns(ordered_profiles, PROFILE_REPORT_COLUMNS)


def build_recommendations_report_frame(recommendations: pd.DataFrame) -> pd.DataFrame:
    if recommendations.empty:
        return recommendations.copy()

    if "has_actionable_recommendation" in recommendations.columns:
        filtered_recommendations = recommendations.loc[recommendations["has_actionable_recommendation"] == 1].copy()
    else:
        filtered_recommendations = recommendations.loc[recommendations["recommendation_count"] > 0].copy()

    if filtered_recommendations.empty:
        return filtered_recommendations

    filtered_recommendations = filtered_recommendations.sort_values(
        ["recommendation_priority", "actionable_recommendation_count", "spend_to_income_ratio", "account_id"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    filtered_recommendations.insert(0, "recommendation_rank", range(1, len(filtered_recommendations) + 1))
    filtered_recommendations = filtered_recommendations.drop(columns=["recommendations"], errors="ignore")
    return _reindex_columns(filtered_recommendations, RECOMMENDATION_REPORT_COLUMNS)


def build_summary(
    scored_transactions: pd.DataFrame,
    account_profiles: pd.DataFrame | None = None,
    recommendations: pd.DataFrame | None = None,
) -> dict[str, int | str]:
    summary: dict[str, int | str] = {
        "total_transactions": int(len(scored_transactions)),
        "total_accounts": int(scored_transactions["account_id"].nunique()),
        "anomalies_detected": int(scored_transactions["is_anomaly"].sum()),
    }

    if not scored_transactions.empty and "timestamp" in scored_transactions.columns:
        summary["analysis_start"] = str(scored_transactions["timestamp"].min())
        summary["analysis_end"] = str(scored_transactions["timestamp"].max())

    if "is_fraud" in scored_transactions.columns:
        summary["labeled_frauds"] = int(scored_transactions["is_fraud"].sum())
        summary["labeled_frauds_flagged"] = int(
            scored_transactions.loc[scored_transactions["is_anomaly"] == 1, "is_fraud"].sum(),
        )

    if "explanation_count" in scored_transactions.columns:
        summary["anomalies_explained"] = int(
            scored_transactions.loc[scored_transactions["is_anomaly"] == 1, "explanation_count"].gt(0).sum(),
        )

    if account_profiles is not None and not account_profiles.empty:
        summary["profiles_generated"] = int(len(account_profiles))

    if recommendations is not None and not recommendations.empty:
        recommendation_report = build_recommendations_report_frame(recommendations)
        summary["accounts_with_recommendations"] = int(len(recommendation_report))
        if "actionable_recommendation_count" in recommendation_report.columns:
            summary["total_recommendations"] = int(recommendation_report["actionable_recommendation_count"].sum())
        else:
            summary["total_recommendations"] = int(len(recommendation_report))

    return summary


def select_top_anomalies(scored_transactions: pd.DataFrame, top_n: int) -> pd.DataFrame:
    anomaly_report = build_anomaly_report_frame(scored_transactions)
    return anomaly_report.head(top_n).reset_index(drop=True)


def save_anomaly_report(scored_transactions: pd.DataFrame, output_path: str | Path | None = None) -> Path:
    resolved_path = Path(output_path) if output_path else DEFAULT_REPORT_PATH
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    anomaly_report = build_anomaly_report_frame(scored_transactions)
    _serialize_for_export(anomaly_report).to_csv(resolved_path, index=False)
    return resolved_path


def save_account_profiles(account_profiles: pd.DataFrame, output_path: str | Path | None = None) -> Path:
    resolved_path = Path(output_path) if output_path else DEFAULT_PROFILE_REPORT_PATH
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    profiles_report = build_account_profiles_report_frame(account_profiles)
    _serialize_for_export(profiles_report).to_csv(resolved_path, index=False)
    return resolved_path


def save_financial_recommendations(
    recommendations: pd.DataFrame,
    output_path: str | Path | None = None,
) -> Path:
    resolved_path = Path(output_path) if output_path else DEFAULT_RECOMMENDATIONS_PATH
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    recommendation_report = build_recommendations_report_frame(recommendations)
    _serialize_for_export(recommendation_report).to_csv(resolved_path, index=False)
    return resolved_path


def select_featured_recommendations(recommendations: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    recommendation_report = build_recommendations_report_frame(recommendations)
    return recommendation_report.head(top_n).reset_index(drop=True)


def format_generation_report(summary: dict[str, object]) -> str:
    average_transactions = 0.0
    if summary["accounts_count"]:
        average_transactions = float(summary["transactions_count"]) / float(summary["accounts_count"])

    lines = [
        "=" * 72,
        "GERACAO DE DADOS SINTETICOS CONCLUIDA",
        "=" * 72,
        "",
        "Resumo da simulacao:",
        f"- Periodo simulado: {summary['start_date']} ate {summary['end_date']}",
        f"- Contas geradas: {summary['accounts_count']}",
        f"- Transacoes geradas: {summary['transactions_count']}",
        f"- Media de transacoes por conta: {average_transactions:.2f}",
        f"- Transacoes rotuladas como fraude: {summary['fraud_transactions']}",
        f"- Taxa de fraude configurada: {summary['fraud_rate']:.2%}",
        "",
        "Arquivos gerados:",
        f"- Contas: {summary['accounts_path']}",
        f"- Transacoes: {summary['transactions_path']}",
        "",
        "Proximo passo sugerido:",
        "- Rode: python main.py",
    ]
    return "\n".join(lines)


def format_console_report(
    dataset_path: Path,
    report_path: Path,
    profiles_path: Path,
    recommendations_path: Path,
    summary: dict[str, int | str],
    top_anomalies: pd.DataFrame,
    featured_recommendations: pd.DataFrame,
) -> str:
    lines = [
        "=" * 72,
        "RELATORIO DE INTELIGENCIA FINANCEIRA",
        "=" * 72,
        "",
        "Resumo da execucao:",
        "- Fonte analisada: dataset sintetico gerado internamente",
        f"- Arquivo analisado: {dataset_path}",
        f"- Transacoes analisadas: {summary['total_transactions']}",
        f"- Contas analisadas: {summary['total_accounts']}",
        f"- Anomalias detectadas: {summary['anomalies_detected']}",
    ]

    if "analysis_start" in summary and "analysis_end" in summary:
        lines.append(f"- Periodo analisado: {summary['analysis_start']} ate {summary['analysis_end']}")

    if "anomalies_explained" in summary:
        lines.append(f"- Anomalias com explicacao: {summary['anomalies_explained']}")

    if "accounts_with_recommendations" in summary:
        lines.append(f"- Contas com recomendacoes acionaveis: {summary['accounts_with_recommendations']}")
        lines.append(f"- Total de recomendacoes acionaveis: {summary['total_recommendations']}")

    if "labeled_frauds" in summary:
        lines.append(f"- Fraudes rotuladas no dataset: {summary['labeled_frauds']}")
        lines.append(f"- Fraudes rotuladas detectadas pelo modelo: {summary['labeled_frauds_flagged']}")

    lines.append("")
    lines.append("Relatorios salvos:")
    lines.append(f"- Anomalias: {report_path}")
    lines.append(f"- Perfis financeiros: {profiles_path}")
    lines.append(f"- Recomendacoes financeiras: {recommendations_path}")
    lines.append("")
    lines.append("Top anomalias:")

    if top_anomalies.empty:
        lines.append("- Nenhuma anomalia foi detectada com a configuracao atual.")
    else:
        for row in top_anomalies.itertuples(index=False):
            fraud_marker = ""
            if hasattr(row, "is_fraud") and row.is_fraud in (0, 1):
                fraud_marker = f" | fraude_rotulada: {row.is_fraud}"

            lines.append(
                f"{row.anomaly_rank}. conta: {row.account_id} | valor: {row.amount:.2f} | "
                f"score: {row.anomaly_score:.2f} | tipo: {row.transaction_type} | "
                f"local: {row.location} | data_hora: {row.timestamp}{fraud_marker}",
            )

            if hasattr(row, "anomaly_explanation") and row.anomaly_explanation:
                lines.append(f"   motivo: {row.anomaly_explanation}")

    lines.append("")
    lines.append("Recomendacoes em destaque:")

    if featured_recommendations.empty:
        lines.append("- Nenhuma recomendacao acionavel foi gerada para o periodo analisado.")
        return "\n".join(lines)

    for row in featured_recommendations.itertuples(index=False):
        lines.append(
            f"{row.recommendation_rank}. conta: {row.account_id} | "
            f"categoria_principal: {row.top_spending_category} | "
            f"risco: {row.recommendation_priority:.2f}",
        )
        lines.append(f"   recomendacao: {row.recommendations_text}")

    return "\n".join(lines)
