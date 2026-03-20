# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Path e usado para montar o caminho do relatorio final.
from pathlib import Path

# Pandas representa e manipula o dataset de saida.
import pandas as pd

# Importa o caminho padrao do relatorio para reaproveitar a configuracao central.
from src.config import DEFAULT_REPORT_PATH


def build_summary(scored_transactions: pd.DataFrame) -> dict[str, int]:
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
    report_frame.to_csv(resolved_path, index=False)
    # Retorna o caminho final salvo.
    return resolved_path


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
    summary: dict[str, int],
    top_anomalies: pd.DataFrame,
) -> str:
    # Monta o cabecalho principal do relatorio de analise.
    lines = [
        "=" * 72,
        "RELATORIO DE ANALISE DE ANOMALIAS",
        "=" * 72,
        "",
        "Resumo da execucao:",
        f"- Dataset analisado: {dataset_path}",
        f"- Transacoes analisadas: {summary['total_transactions']}",
        f"- Contas analisadas: {summary['total_accounts']}",
        f"- Anomalias detectadas: {summary['anomalies_detected']}",
    ]

    # Quando houver rotulo de fraude no dataset, mostra um resumo adicional.
    if "labeled_frauds" in summary:
        lines.append(f"- Fraudes rotuladas no dataset: {summary['labeled_frauds']}")
        lines.append(f"- Fraudes rotuladas detectadas pelo modelo: {summary['labeled_frauds_flagged']}")

    # Mostra onde o CSV final foi salvo.
    lines.append(f"- Relatorio CSV salvo em: {report_path}")
    lines.append("")
    lines.append("Ranking das transacoes mais suspeitas:")

    # Se nada foi marcado, informa isso claramente no terminal.
    if top_anomalies.empty:
        lines.append("- Nenhuma anomalia foi detectada com a configuracao atual.")
        return "\n".join(lines)

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
            f"local: {row.location} | data_hora: {row.timestamp}{fraud_marker}"
        )
        # Atualiza a numeracao do ranking.
        position += 1

    # Retorna o bloco final pronto para impressao.
    return "\n".join(lines)
