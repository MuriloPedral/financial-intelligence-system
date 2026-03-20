from __future__ import annotations

import argparse
from pathlib import Path

from src.config import (
    AnalysisConfig,
    DEFAULT_PROFILE_REPORT_PATH,
    DEFAULT_RECOMMENDATIONS_PATH,
    DEFAULT_REPORT_PATH,
    ensure_project_directories,
)
from src.dataset.load_dataset import load_transaction_dataset
from src.explainability.anomaly_explainer import explain_anomalies
from src.features.feature_engineering import engineer_transaction_features
from src.models.anomaly_detection import detect_anomalies
from src.profiles.account_profiles import build_account_profiles
from src.recommendations.financial_recommendations import build_financial_recommendations
from src.reporting.report_generator import (
    build_summary,
    format_console_report,
    save_account_profiles,
    save_anomaly_report,
    save_financial_recommendations,
    select_featured_recommendations,
    select_top_anomalies,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa a analise do Financial Intelligence System usando apenas o dataset sintetico gerado internamente.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Caminho CSV de saida para o relatorio de anomalias.",
    )
    parser.add_argument(
        "--profiles-output-path",
        type=Path,
        default=DEFAULT_PROFILE_REPORT_PATH,
        help="Caminho CSV de saida para os perfis financeiros por conta.",
    )
    parser.add_argument(
        "--recommendations-output-path",
        type=Path,
        default=DEFAULT_RECOMMENDATIONS_PATH,
        help="Caminho CSV de saida para as recomendacoes financeiras por conta.",
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.03,
        help="Proporcao esperada de anomalias para o Isolation Forest.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Quantidade de transacoes suspeitas exibidas no ranking.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente usada pelo modelo para reproducao.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_project_directories()

    analysis_config = AnalysisConfig(
        contamination=args.contamination,
        top_n=args.top_n,
        random_state=args.seed,
    )

    transactions, dataset_path = load_transaction_dataset()
    enriched_transactions, feature_matrix = engineer_transaction_features(transactions)
    account_profiles = build_account_profiles(enriched_transactions)
    scored_transactions, _ = detect_anomalies(enriched_transactions, feature_matrix, analysis_config)
    explained_transactions = explain_anomalies(scored_transactions, account_profiles)
    recommendations = build_financial_recommendations(account_profiles)

    report_path = save_anomaly_report(explained_transactions, output_path=args.output_path)
    profiles_path = save_account_profiles(account_profiles, output_path=args.profiles_output_path)
    recommendations_path = save_financial_recommendations(
        recommendations,
        output_path=args.recommendations_output_path,
    )
    summary = build_summary(explained_transactions, account_profiles, recommendations)
    top_anomalies = select_top_anomalies(explained_transactions, top_n=analysis_config.top_n)
    featured_recommendations = select_featured_recommendations(recommendations)

    print(
        format_console_report(
            dataset_path,
            report_path,
            profiles_path,
            recommendations_path,
            summary,
            top_anomalies,
            featured_recommendations,
        ),
    )


if __name__ == "__main__":
    main()
