from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
GENERATED_DATA_DIR = RAW_DATA_DIR / "generated"
REPORTS_DIR = DATA_DIR / "reports"

DEFAULT_ACCOUNTS_PATH = GENERATED_DATA_DIR / "accounts.csv"
DEFAULT_TRANSACTIONS_PATH = GENERATED_DATA_DIR / "transactions.csv"
DEFAULT_REPORT_PATH = REPORTS_DIR / "anomaly_report.csv"
DEFAULT_PROFILE_REPORT_PATH = REPORTS_DIR / "account_profiles.csv"
DEFAULT_RECOMMENDATIONS_PATH = REPORTS_DIR / "financial_recommendations.csv"


def ensure_project_directories() -> None:
    for path in (RAW_DATA_DIR, GENERATED_DATA_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    accounts_count: int = 150
    months: int = 6
    fraud_rate: float = 0.03
    seed: int = 42
    start_date: date | None = None
    end_date: date | None = None

    def validate(self) -> None:
        if self.accounts_count <= 0:
            msg = "A quantidade de contas deve ser maior que zero."
            raise ValueError(msg)
        if self.months <= 0 and (self.start_date is None or self.end_date is None):
            msg = "A quantidade de meses deve ser maior que zero quando as datas nao forem informadas."
            raise ValueError(msg)
        if not 0 <= self.fraud_rate <= 1:
            msg = "A taxa de fraude deve ficar entre 0 e 1."
            raise ValueError(msg)

    def resolve_dates(self) -> tuple[date, date]:
        self.validate()
        resolved_end = self.end_date or date.today()
        resolved_start = self.start_date or (resolved_end - timedelta(days=self.months * 30))
        if resolved_start > resolved_end:
            msg = "A data inicial nao pode ser maior que a data final."
            raise ValueError(msg)
        return resolved_start, resolved_end


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    contamination: float = 0.03
    top_n: int = 10
    random_state: int = 42

    def validate(self) -> None:
        if not 0 < self.contamination <= 0.5:
            msg = "O parametro contamination deve ficar entre 0 e 0.5."
            raise ValueError(msg)
        if self.top_n <= 0:
            msg = "A quantidade de itens do ranking deve ser maior que zero."
            raise ValueError(msg)
