# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Biblioteca para construir a CLI.
import argparse
# Path representa caminhos de arquivo.
from pathlib import Path

# Importa a configuracao central da etapa de analise.
from src.config import (
    AnalysisConfig,
    DEFAULT_PROFILE_REPORT_PATH,
    DEFAULT_RECOMMENDATIONS_PATH,
    DEFAULT_REPORT_PATH,
    ensure_project_directories,
)
# Importa a etapa de carga e validacao do dataset.
from src.dataset.load_dataset import load_transaction_dataset
# Importa a camada de explicabilidade das anomalias detectadas.
from src.explainability.anomaly_explainer import explain_anomalies
# Importa a etapa que transforma os dados em features numericas.
from src.features.feature_engineering import engineer_transaction_features
# Importa o modelo de deteccao de anomalias.
from src.models.anomaly_detection import detect_anomalies
# Importa a etapa de construcao de perfis financeiros por conta.
from src.profiles.account_profiles import build_account_profiles
# Importa a etapa de recomendacoes financeiras.
from src.recommendations.financial_recommendations import build_financial_recommendations
# Importa as funcoes que montam e salvam o relatorio final.
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
    # Cria a interface de linha de comando da etapa analitica.
    parser = argparse.ArgumentParser(
        description="Executa o MVP de deteccao de anomalias do Financial Intelligence System.",
    )
    parser.add_argument(
        "--input-path",
        type=str,
        default=None,
        help="Caminho opcional para o CSV de transacoes.",
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
    # Retorna os argumentos preenchidos.
    return parser.parse_args()


def main() -> None:
    # Le os argumentos passados pelo usuario.
    args = parse_args()
    # Garante a existencia das pastas do projeto.
    ensure_project_directories()

    # Monta a configuracao do modelo de anomalias.
    analysis_config = AnalysisConfig(
        contamination=args.contamination,
        top_n=args.top_n,
        random_state=args.seed,
    )

    # Carrega e valida o dataset que sera analisado.
    transactions, dataset_path = load_transaction_dataset(args.input_path)
    # Converte as transacoes em variaveis numericas e categoricas tratadas.
    enriched_transactions, feature_matrix = engineer_transaction_features(transactions)
    # Construi o perfil financeiro de cada conta antes de rodar a camada de explicabilidade.
    account_profiles = build_account_profiles(enriched_transactions)
    # Aplica o modelo e devolve o score de anomalia para cada linha.
    scored_transactions, _ = detect_anomalies(enriched_transactions, feature_matrix, analysis_config)
    # Traduz cada anomalia em motivos legiveis baseados no perfil da conta.
    explained_transactions = explain_anomalies(scored_transactions, account_profiles)
    # Gera recomendacoes simples e personalizadas a partir do perfil financeiro.
    recommendations = build_financial_recommendations(account_profiles)

    # Salva o CSV final com todas as transacoes pontuadas.
    report_path = save_anomaly_report(explained_transactions, output_path=args.output_path)
    # Salva o CSV com o perfil financeiro consolidado por conta.
    profiles_path = save_account_profiles(account_profiles, output_path=args.profiles_output_path)
    # Salva o CSV com as recomendacoes financeiras por conta.
    recommendations_path = save_financial_recommendations(
        recommendations,
        output_path=args.recommendations_output_path,
    )
    # Resume a execucao em numeros agregados.
    summary = build_summary(explained_transactions, account_profiles, recommendations)
    # Seleciona as transacoes mais suspeitas para mostrar no terminal.
    top_anomalies = select_top_anomalies(explained_transactions, top_n=analysis_config.top_n)
    # Separa algumas recomendacoes para destacar no terminal.
    featured_recommendations = select_featured_recommendations(recommendations)

    # Imprime o relatorio textual final no terminal.
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
    # Executa o fluxo principal quando o arquivo e chamado diretamente.
    main()
