# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Biblioteca para criar interface de linha de comando.
import argparse
# date converte datas de texto para objetos Python.
from datetime import date
# Path representa caminhos de arquivo de forma segura.
from pathlib import Path

# Importa caminhos padrao e a configuracao central da geracao.
from src.config import (
    DEFAULT_ACCOUNTS_PATH,
    DEFAULT_TRANSACTIONS_PATH,
    GenerationConfig,
    ensure_project_directories,
)
# Importa as funcoes ligadas ao ciclo de vida das contas.
from src.generators.account_generator import (
    generate_accounts,
    save_accounts,
    sync_account_balances,
    validate_accounts,
)
# Importa as funcoes ligadas ao ciclo de vida das transacoes.
from src.generators.transaction_generator import generate_transactions, save_transactions, validate_transactions
# Importa o formatador do resumo final para o terminal.
from src.reporting.report_generator import format_generation_report


def _parse_optional_date(value: str | None) -> date | None:
    # Quando o usuario nao informa data, mantem o valor ausente.
    if not value:
        return None
    # Converte a string no formato YYYY-MM-DD para um objeto date.
    return date.fromisoformat(value)


def parse_args() -> argparse.Namespace:
    # Cria a interface principal de linha de comando para a geracao.
    parser = argparse.ArgumentParser(description="Gera contas e transacoes financeiras sinteticas.")
    # Permite definir quantas contas serao criadas.
    parser.add_argument("--accounts", type=int, default=150, help="Quantidade de contas a gerar.")
    # Permite definir quantos meses serao simulados.
    parser.add_argument("--months", type=int, default=6, help="Quantidade de meses a simular.")
    # Permite configurar a taxa aproximada de fraude.
    parser.add_argument("--fraud-rate", type=float, default=0.03, help="Taxa aproximada de fraude a injetar.")
    # Define a semente para reproducao.
    parser.add_argument("--seed", type=int, default=42, help="Semente para reproducao dos resultados.")
    # Permite informar manualmente a data inicial do periodo.
    parser.add_argument("--start-date", type=str, default=None, help="Data inicial opcional no formato YYYY-MM-DD.")
    # Permite informar manualmente a data final do periodo.
    parser.add_argument("--end-date", type=str, default=None, help="Data final opcional no formato YYYY-MM-DD.")
    parser.add_argument(
        "--accounts-output",
        type=Path,
        default=DEFAULT_ACCOUNTS_PATH,
        help="Caminho CSV de saida para as contas geradas.",
    )
    parser.add_argument(
        "--transactions-output",
        type=Path,
        default=DEFAULT_TRANSACTIONS_PATH,
        help="Caminho CSV de saida para as transacoes geradas.",
    )
    # Retorna os argumentos preenchidos pelo usuario.
    return parser.parse_args()


def main() -> None:
    # Le os argumentos passados no terminal.
    args = parse_args()
    # Garante a existencia das pastas necessarias antes de salvar arquivos.
    ensure_project_directories()

    # Cria a configuracao da simulacao com os parametros escolhidos.
    config = GenerationConfig(
        accounts_count=args.accounts,
        months=args.months,
        fraud_rate=args.fraud_rate,
        seed=args.seed,
        start_date=_parse_optional_date(args.start_date),
        end_date=_parse_optional_date(args.end_date),
    )
    # Valida a configuracao para evitar execucao com parametros invalidos.
    config.validate()
    # Resolve o intervalo de datas real que sera usado na simulacao.
    start_date, end_date = config.resolve_dates()

    # Gera a base de contas sinteticas.
    accounts = generate_accounts(config.accounts_count, seed=config.seed)
    # Gera as transacoes simuladas com base no comportamento das contas.
    transactions = generate_transactions(accounts, config)
    # Ajusta o saldo atual de cada conta para bater com a ultima transacao registrada.
    sync_account_balances(accounts, transactions)
    # Valida a integridade do dataset de contas.
    validate_accounts(accounts)
    # Valida a integridade do dataset de transacoes.
    validate_transactions(transactions)

    # Salva o CSV final de contas.
    accounts_path = save_accounts(accounts, output_path=args.accounts_output)
    # Salva o CSV final de transacoes.
    transactions_path = save_transactions(transactions, output_path=args.transactions_output)

    # Conta quantas transacoes foram rotuladas como fraude para mostrar no resumo.
    fraud_transactions = sum(int(transaction.get("is_fraud", 0)) for transaction in transactions)
    # Monta o objeto de resumo que sera exibido no terminal.
    summary = {
        "start_date": start_date,
        "end_date": end_date,
        "accounts_count": len(accounts),
        "transactions_count": len(transactions),
        "fraud_transactions": fraud_transactions,
        "fraud_rate": config.fraud_rate,
        "accounts_path": accounts_path,
        "transactions_path": transactions_path,
    }
    # Imprime uma saida mais organizada e amigavel para o usuario.
    print(format_generation_report(summary))


if __name__ == "__main__":
    # Executa o script apenas quando ele for chamado diretamente pelo terminal.
    main()
