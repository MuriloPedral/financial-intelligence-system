from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from src.config import (
    DEFAULT_ACCOUNTS_PATH,
    DEFAULT_TRANSACTIONS_PATH,
    GenerationConfig,
    ensure_project_directories,
)
from src.generators.account_generator import (
    generate_accounts,
    save_accounts,
    sync_account_balances,
    validate_accounts,
)
from src.generators.transaction_generator import generate_transactions, save_transactions, validate_transactions
from src.reporting.report_generator import format_generation_report


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera contas e transacoes financeiras sinteticas.")
    parser.add_argument("--accounts", type=int, default=150, help="Quantidade de contas a gerar.")
    parser.add_argument("--months", type=int, default=6, help="Quantidade de meses a simular.")
    parser.add_argument("--fraud-rate", type=float, default=0.03, help="Taxa aproximada de fraude a injetar.")
    parser.add_argument("--seed", type=int, default=42, help="Semente para reproducao dos resultados.")
    parser.add_argument("--start-date", type=str, default=None, help="Data inicial opcional no formato YYYY-MM-DD.")
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_project_directories()

    config = GenerationConfig(
        accounts_count=args.accounts,
        months=args.months,
        fraud_rate=args.fraud_rate,
        seed=args.seed,
        start_date=_parse_optional_date(args.start_date),
        end_date=_parse_optional_date(args.end_date),
    )
    config.validate()
    start_date, end_date = config.resolve_dates()

    accounts = generate_accounts(config.accounts_count, seed=config.seed)
    transactions = generate_transactions(accounts, config)
    sync_account_balances(accounts, transactions)
    validate_accounts(accounts)
    validate_transactions(transactions)

    accounts_path = save_accounts(accounts, output_path=args.accounts_output)
    transactions_path = save_transactions(transactions, output_path=args.transactions_output)

    fraud_transactions = sum(int(transaction.get("is_fraud", 0)) for transaction in transactions)
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
    print(format_generation_report(summary))


if __name__ == "__main__":
    main()
