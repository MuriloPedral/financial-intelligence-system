# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# json e usado para serializar o dicionario de categorias no CSV.
import json
# Path representa caminhos de arquivo de forma segura.
from pathlib import Path

# Pandas transforma a lista de contas em tabela tabular.
import pandas as pd

# Importa o caminho padrao do arquivo de contas.
from src.config import DEFAULT_ACCOUNTS_PATH
# Importa utilitarios de aleatoriedade usados na criacao das contas.
from src.utils.random_utils import build_rng, normalize_weights, sample_without_replacement


# Lista de categorias de gasto usadas para montar preferencia de consumo.
SPENDING_CATEGORIES = [
    "groceries",
    "restaurant",
    "transport",
    "entertainment",
    "utilities",
    "health",
    "shopping",
    "travel",
]

# Distribuicao de cidades de origem das contas.
CITY_WEIGHTS = {
    "Aracaju": 0.44,
    "Sao Cristovao": 0.12,
    "Barra dos Coqueiros": 0.10,
    "Nossa Senhora do Socorro": 0.12,
    "Estancia": 0.08,
    "Itabaiana": 0.07,
    "Lagarto": 0.07,
}

# Distribuicao do nivel de atividade financeira das contas.
ACTIVITY_WEIGHTS = {"low": 0.28, "medium": 0.50, "high": 0.22}
# Faixa de transacoes por dia para cada nivel de atividade.
ACTIVITY_RANGES = {"low": (2, 3), "medium": (4, 6), "high": (7, 10)}

# Faixas salariais usadas para simular perfis economicos diferentes.
SALARY_BANDS = (
    ("low", 1800.0, 3200.0, 0.48),
    ("medium", 3200.0, 7800.0, 0.37),
    ("high", 7800.0, 16500.0, 0.15),
)

# Janelas de horario normalmente usadas por cada tipo de perfil.
ACTIVE_WINDOWS = {
    "day": (6, 20),
    "mixed": (8, 23),
    "night": (18, 3),
}


def _choose_home_city(rng) -> str:
    # Separa o nome das cidades.
    cities = list(CITY_WEIGHTS.keys())
    # Separa os pesos correspondentes.
    weights = list(CITY_WEIGHTS.values())
    # Sorteia uma cidade respeitando a distribuicao configurada.
    return rng.choices(cities, weights=weights, k=1)[0]


def _choose_activity_profile(rng) -> tuple[str, int]:
    # Separa os niveis de atividade.
    levels = list(ACTIVITY_WEIGHTS.keys())
    # Separa os pesos de cada nivel.
    weights = list(ACTIVITY_WEIGHTS.values())
    # Escolhe um nivel para a conta.
    activity_level = rng.choices(levels, weights=weights, k=1)[0]
    # Recupera a faixa de transacoes permitida para esse nivel.
    tx_min, tx_max = ACTIVITY_RANGES[activity_level]
    # Retorna o nivel e um valor concreto de transacoes por dia.
    return activity_level, rng.randint(tx_min, tx_max)


def _generate_salary(rng) -> float:
    # Escolhe a faixa salarial da conta.
    salary_band = rng.choices(
        [band_name for band_name, *_ in SALARY_BANDS],
        weights=[weight for *_, weight in SALARY_BANDS],
        k=1,
    )[0]

    # Procura a faixa escolhida para gerar um salario dentro do intervalo correto.
    for band_name, lower_bound, upper_bound, _ in SALARY_BANDS:
        if salary_band == band_name:
            return round(rng.uniform(lower_bound, upper_bound), 2)

    # Esse erro so deveria acontecer se a configuracao das faixas estiver inconsistente.
    msg = "Nao foi possivel determinar a faixa salarial."
    raise RuntimeError(msg)


def _generate_category_weights(rng) -> dict[str, float]:
    # Escolhe tres categorias favoritas sem repeticao.
    favorite_categories = sample_without_replacement(SPENDING_CATEGORIES, sample_size=3, rng=rng)
    # Gera pesos brutos aleatorios para essas categorias.
    raw_weights = {category: rng.uniform(0.2, 1.0) for category in favorite_categories}
    # Normaliza os pesos para a soma final ser 1.
    normalized = normalize_weights(raw_weights)
    # Arredonda os pesos para deixar o CSV mais limpo.
    return {category: round(weight, 4) for category, weight in normalized.items()}


def generate_account(account_number: int, seed: int | None = None) -> dict[str, object]:
    # Cria um gerador pseudoaleatorio exclusivo da conta.
    rng = build_rng(seed if seed is not None else account_number)
    # Gera o salario da conta.
    salary = _generate_salary(rng)
    # Define o perfil de atividade e a media diaria de transacoes.
    activity_level, transactions_per_day = _choose_activity_profile(rng)
    # Escolhe se a conta opera mais de dia, de forma mista ou a noite.
    active_profile = rng.choices(["day", "mixed", "night"], weights=[0.56, 0.30, 0.14], k=1)[0]
    # Recupera a janela horaria correspondente ao perfil escolhido.
    active_hour_start, active_hour_end = ACTIVE_WINDOWS[active_profile]
    # Calcula o saldo inicial a partir do salario.
    initial_balance = round(salary * rng.uniform(0.8, 3.4), 2)

    # Retorna um dicionario completo com o perfil comportamental da conta.
    return {
        "account_id": f"A{account_number:05d}",
        "home_city": _choose_home_city(rng),
        "initial_balance": initial_balance,
        "current_balance": initial_balance,
        "salary": salary,
        "salary_day": rng.randint(1, 5),
        "activity_level": activity_level,
        "transactions_per_day": transactions_per_day,
        "favorite_categories": _generate_category_weights(rng),
        "active_hour_start": active_hour_start,
        "active_hour_end": active_hour_end,
    }


def generate_accounts(accounts_count: int, seed: int | None = None) -> list[dict[str, object]]:
    # Cria um gerador mestre para que o conjunto inteiro possa ser reproduzido.
    master_rng = build_rng(seed)
    # Inicializa a lista final de contas.
    accounts = []
    # Gera uma conta por iteracao.
    for index in range(1, accounts_count + 1):
        # Cria uma semente derivada para cada conta ter variacao interna.
        account_seed = master_rng.randint(1, 10_000_000)
        accounts.append(generate_account(index, seed=account_seed))
    # Devolve a colecao completa.
    return accounts


def accounts_to_frame(accounts: list[dict[str, object]]) -> pd.DataFrame:
    # Converte a lista de dicionarios em DataFrame.
    frame = pd.DataFrame(accounts)
    # Serializa as categorias favoritas para caberem em uma unica coluna de texto.
    if "favorite_categories" in frame.columns:
        frame["favorite_categories"] = frame["favorite_categories"].apply(
            lambda value: json.dumps(value, sort_keys=True),
        )
    # Retorna a tabela pronta para exportacao.
    return frame


def sync_account_balances(
    accounts: list[dict[str, object]],
    transactions: list[dict[str, object]] | pd.DataFrame,
) -> list[dict[str, object]]:
    # Aceita tanto lista quanto DataFrame e converte quando necessario.
    if isinstance(transactions, pd.DataFrame):
        transactions_frame = transactions.copy()
    else:
        transactions_frame = pd.DataFrame(transactions)

    # Se nao houver transacoes, nao ha saldo final para sincronizar.
    if transactions_frame.empty:
        return accounts

    # Recupera o ultimo balance_after de cada conta.
    final_balances = (
        transactions_frame.sort_values(["account_id", "timestamp"])
        .groupby("account_id", sort=False)["balance_after"]
        .last()
        .to_dict()
    )

    # Atualiza o current_balance de cada conta com o saldo final observado.
    for account in accounts:
        account_id = str(account["account_id"])
        if account_id in final_balances:
            account["current_balance"] = round(float(final_balances[account_id]), 2)

    # Retorna a mesma lista de contas agora sincronizada.
    return accounts


def validate_accounts(accounts: list[dict[str, object]] | pd.DataFrame) -> None:
    # Normaliza a entrada para DataFrame.
    accounts_frame = accounts.copy() if isinstance(accounts, pd.DataFrame) else accounts_to_frame(accounts)
    # Nao faz sentido salvar um dataset vazio.
    if accounts_frame.empty:
        msg = "O dataset de contas gerado esta vazio."
        raise ValueError(msg)
    # Cada conta precisa de um identificador unico.
    if accounts_frame["account_id"].duplicated().any():
        msg = "Foram encontrados account_id duplicados no dataset de contas."
        raise ValueError(msg)
    # Define as colunas minimas exigidas.
    required_columns = {"account_id", "initial_balance", "current_balance", "salary", "favorite_categories"}
    # Verifica o que esta faltando.
    missing_columns = required_columns.difference(accounts_frame.columns)
    if missing_columns:
        formatted_columns = ", ".join(sorted(missing_columns))
        msg = f"O dataset de contas nao possui as colunas obrigatorias: {formatted_columns}"
        raise ValueError(msg)


def save_accounts(accounts: list[dict[str, object]], output_path: Path | None = None) -> Path:
    # Usa o caminho informado ou o caminho padrao do projeto.
    resolved_path = output_path or DEFAULT_ACCOUNTS_PATH
    # Garante que a pasta exista antes de salvar.
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    # Exporta o DataFrame para CSV sem indice numerico.
    accounts_to_frame(accounts).to_csv(resolved_path, index=False)
    # Retorna o caminho final salvo.
    return resolved_path
