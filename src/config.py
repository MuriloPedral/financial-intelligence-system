# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Dataclass simplifica a criacao de objetos de configuracao.
from dataclasses import dataclass
# date e timedelta ajudam a calcular o periodo da simulacao.
from datetime import date, timedelta
# Path permite lidar com caminhos de arquivos de forma portavel.
from pathlib import Path


# Pasta raiz do projeto.
ROOT_DIR = Path(__file__).resolve().parents[1]
# Pasta principal de dados.
DATA_DIR = ROOT_DIR / "data"
# Pasta reservada para datasets de entrada e saida bruta.
RAW_DATA_DIR = DATA_DIR / "raw"
# Pasta onde os arquivos gerados automaticamente sao salvos.
GENERATED_DATA_DIR = RAW_DATA_DIR / "generated"
# Pasta onde os relatorios analiticos sao exportados.
REPORTS_DIR = DATA_DIR / "reports"

# Caminho padrao para um dataset publico externo, se existir.
DEFAULT_PUBLIC_DATASET_PATH = RAW_DATA_DIR / "financial_transactions.csv"
# Caminho padrao das contas sinteticas geradas.
DEFAULT_ACCOUNTS_PATH = GENERATED_DATA_DIR / "accounts.csv"
# Caminho padrao das transacoes sinteticas geradas.
DEFAULT_TRANSACTIONS_PATH = GENERATED_DATA_DIR / "transactions.csv"
# Caminho padrao do relatorio final de anomalias.
DEFAULT_REPORT_PATH = REPORTS_DIR / "anomaly_report.csv"
# Caminho padrao do arquivo de perfis financeiros por conta.
DEFAULT_PROFILE_REPORT_PATH = REPORTS_DIR / "account_profiles.csv"
# Caminho padrao do arquivo de recomendacoes financeiras por conta.
DEFAULT_RECOMMENDATIONS_PATH = REPORTS_DIR / "financial_recommendations.csv"


def ensure_project_directories() -> None:
    # Garante que todas as pastas do projeto existam antes de salvar arquivos.
    for path in (RAW_DATA_DIR, GENERATED_DATA_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    # Quantidade de contas sinteticas que sera criada.
    accounts_count: int = 150
    # Quantidade de meses simulados quando datas explicitas nao sao passadas.
    months: int = 6
    # Probabilidade aproximada de injetar comportamento suspeito.
    fraud_rate: float = 0.03
    # Semente para reproduzir os mesmos resultados.
    seed: int = 42
    # Data inicial opcional da simulacao.
    start_date: date | None = None
    # Data final opcional da simulacao.
    end_date: date | None = None

    def validate(self) -> None:
        # Impede geracao sem contas.
        if self.accounts_count <= 0:
            msg = "A quantidade de contas deve ser maior que zero."
            raise ValueError(msg)
        # Exige ao menos um mes quando o periodo nao foi informado manualmente.
        if self.months <= 0 and (self.start_date is None or self.end_date is None):
            msg = "A quantidade de meses deve ser maior que zero quando as datas nao forem informadas."
            raise ValueError(msg)
        # A taxa de fraude precisa representar uma probabilidade valida.
        if not 0 <= self.fraud_rate <= 1:
            msg = "A taxa de fraude deve ficar entre 0 e 1."
            raise ValueError(msg)

    def resolve_dates(self) -> tuple[date, date]:
        # Reaproveita as validacoes gerais antes de calcular o periodo.
        self.validate()
        # Usa a data final informada ou, na ausencia dela, a data atual.
        resolved_end = self.end_date or date.today()
        # Usa a data inicial informada ou calcula um intervalo aproximado em meses.
        resolved_start = self.start_date or (resolved_end - timedelta(days=self.months * 30))
        # Impede intervalo invertido.
        if resolved_start > resolved_end:
            msg = "A data inicial nao pode ser maior que a data final."
            raise ValueError(msg)
        # Retorna o periodo efetivo que sera usado na simulacao.
        return resolved_start, resolved_end


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    # Proporcao esperada de anomalias para o Isolation Forest.
    contamination: float = 0.03
    # Quantidade de itens que sera mostrada no ranking final.
    top_n: int = 10
    # Semente de reproducao para o modelo.
    random_state: int = 42

    def validate(self) -> None:
        # O parametro contamination do Isolation Forest deve ficar dentro da faixa suportada.
        if not 0 < self.contamination <= 0.5:
            msg = "O parametro contamination deve ficar entre 0 e 0.5."
            raise ValueError(msg)
        # O ranking precisa ter ao menos um item.
        if self.top_n <= 0:
            msg = "A quantidade de itens do ranking deve ser maior que zero."
            raise ValueError(msg)
