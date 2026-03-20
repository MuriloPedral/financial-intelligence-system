# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# json ajuda a desserializar categorias favoritas vindas do CSV.
import json
# datetime e time ajudam a montar horarios de transacao.
from datetime import datetime, time
# Path representa caminhos de arquivo.
from pathlib import Path
# Any permite aceitar mais de um formato de entrada ao normalizar contas.
from typing import Any

# Pandas manipula a tabela de transacoes.
import pandas as pd

# Importa a configuracao padrao da geracao.
from src.config import DEFAULT_TRANSACTIONS_PATH, GenerationConfig
# Importa utilitarios de sorteio controlado.
from src.utils.random_utils import build_rng, choose_weighted
# Importa utilitarios de datas e timestamps.
from src.utils.time_utils import date_sequence, random_timestamp


# Mapa simples de proximidade geografica para deslocamentos plausiveis.
CITY_NETWORK = {
    "Aracaju": ["Sao Cristovao", "Barra dos Coqueiros", "Nossa Senhora do Socorro"],
    "Sao Cristovao": ["Aracaju", "Barra dos Coqueiros"],
    "Barra dos Coqueiros": ["Aracaju", "Sao Cristovao"],
    "Nossa Senhora do Socorro": ["Aracaju", "Sao Cristovao"],
    "Estancia": ["Lagarto", "Aracaju"],
    "Itabaiana": ["Aracaju", "Lagarto"],
    "Lagarto": ["Estancia", "Aracaju"],
}

# Cidades "distantes" usadas para simular viagens ou localizacoes estranhas.
TRAVEL_CITIES = [
    "Salvador",
    "Maceio",
    "Recife",
    "Fortaleza",
    "Sao Paulo",
    "Rio de Janeiro",
    "Belo Horizonte",
]

# Faixas de valores por categoria de gasto.
CATEGORY_AMOUNT_RANGES = {
    "groceries": (18.0, 260.0),
    "restaurant": (18.0, 190.0),
    "transport": (8.0, 85.0),
    "entertainment": (25.0, 260.0),
    "utilities": (55.0, 420.0),
    "health": (30.0, 480.0),
    "shopping": (45.0, 820.0),
    "travel": (160.0, 2200.0),
    "transfer": (30.0, 1500.0),
    "cash_withdrawal": (40.0, 600.0),
}

# Canais mais provaveis para cada tipo de transacao.
TYPE_CHANNELS = {
    "card_purchase": ["debit_card", "credit_card", "mobile_wallet"],
    "online_purchase": ["internet_banking", "mobile_app", "card_not_present"],
    "pix_out": ["pix"],
    "pix_in": ["pix"],
    "bill_payment": ["mobile_app", "internet_banking"],
    "atm_withdrawal": ["atm"],
    "salary_deposit": ["bank_transfer"],
}


def _coerce_accounts(accounts: Any) -> list[dict[str, Any]]:
    # Aceita tanto DataFrame quanto lista de dicionarios.
    if isinstance(accounts, pd.DataFrame):
        records = accounts.to_dict("records")
    else:
        records = [dict(account) for account in accounts]

    # Aqui sera guardada a versao normalizada de cada conta.
    coerced_accounts = []
    for account in records:
        # Copia a conta para nao alterar a estrutura original de forma inesperada.
        normalized_account = dict(account)
        # Recupera as categorias favoritas.
        favorite_categories = normalized_account.get("favorite_categories", {})
        # Quando elas vierem como texto JSON, desserializa para dicionario.
        if isinstance(favorite_categories, str):
            favorite_categories = json.loads(favorite_categories)

        # Garante os tipos corretos para todas as colunas usadas na simulacao.
        normalized_account["favorite_categories"] = favorite_categories
        normalized_account["salary"] = float(normalized_account["salary"])
        normalized_account["initial_balance"] = float(normalized_account["initial_balance"])
        normalized_account["current_balance"] = float(
            normalized_account.get("current_balance", normalized_account["initial_balance"]),
        )
        normalized_account["transactions_per_day"] = int(normalized_account["transactions_per_day"])
        normalized_account["salary_day"] = int(normalized_account.get("salary_day", 5))
        normalized_account["active_hour_start"] = int(normalized_account["active_hour_start"])
        normalized_account["active_hour_end"] = int(normalized_account["active_hour_end"])
        # Guarda a conta normalizada na lista final.
        coerced_accounts.append(normalized_account)

    # Retorna todas as contas prontas para uso no gerador.
    return coerced_accounts


def _daily_transactions_target(account: dict[str, Any], current_date, rng) -> int:
    # Parte da media diaria configurada na conta.
    base_target = int(account["transactions_per_day"])
    # Cria uma faixa de variacao ao redor da media.
    lower_bound = max(1, base_target - 2)
    upper_bound = base_target + 2
    # Sorteia o volume real daquele dia.
    sampled_target = rng.randint(lower_bound, upper_bound)
    # Fins de semana podem aumentar a atividade de perfis mais ativos.
    if current_date.weekday() >= 5 and account["activity_level"] != "low":
        sampled_target += 1
    # Retorna a quantidade final.
    return sampled_target


def _pick_spending_category(account: dict[str, Any], is_fraud: bool, rng) -> str:
    # Comeca com um peso base minimo para todas as categorias de consumo.
    base_weights = {category: 0.04 for category in CATEGORY_AMOUNT_RANGES if category not in {"transfer", "cash_withdrawal"}}
    # Aumenta os pesos das categorias favoritas da conta.
    base_weights.update(account["favorite_categories"])

    # Em caso de fraude, reforca categorias mais tipicas de comportamento suspeito.
    if is_fraud:
        for category, factor in {"travel": 2.4, "shopping": 2.2, "health": 1.5}.items():
            base_weights[category] = base_weights.get(category, 0.05) * factor

    # Sorteia a categoria final com base nesses pesos.
    return choose_weighted(base_weights, rng)


def _pick_transaction_type(category: str, is_fraud: bool, rng) -> str:
    # Contas de utilidade normalmente viram pagamento de boleto.
    if category == "utilities":
        return "bill_payment"
    # Parte das despesas de transporte pode aparecer como saque.
    if category == "transport" and rng.random() < 0.18:
        return "atm_withdrawal"
    # Viagens tendem a acontecer com compra online, especialmente em fraude.
    if category == "travel" and (is_fraud or rng.random() < 0.45):
        return "online_purchase"
    # Uma parte das saidas vira transferencia instantanea.
    if rng.random() < 0.17:
        return "pix_out"
    # Caso padrao: compra com cartao.
    return "card_purchase"


def _pick_location(account: dict[str, Any], is_fraud: bool, rng) -> str:
    # Recupera a cidade-base da conta.
    home_city = account["home_city"]
    # Recupera cidades proximas plausiveis.
    nearby_cities = CITY_NETWORK.get(home_city, [])

    # Fraudes podem acontecer em cidades distantes do comportamento habitual.
    if is_fraud:
        return rng.choice(TRAVEL_CITIES)
    # Em alguns casos a pessoa transaciona em cidades proximas.
    if nearby_cities and rng.random() < 0.12:
        return rng.choice(nearby_cities)
    # Em poucos casos a pessoa aparece em outra cidade de viagem mesmo sem fraude.
    if rng.random() < 0.03:
        return rng.choice(TRAVEL_CITIES)
    # No restante dos casos, usa a cidade de origem da conta.
    return home_city


def _pick_amount(account: dict[str, Any], category: str, is_fraud: bool, rng) -> float:
    # Recupera a faixa de valores valida para a categoria.
    minimum_amount, maximum_amount = CATEGORY_AMOUNT_RANGES[category]
    # Ajusta o teto com base no nivel de renda da conta.
    salary_factor = max(0.8, min(2.3, account["salary"] / 3800.0))
    # Sorteia um valor dentro da faixa ajustada.
    amount = rng.uniform(minimum_amount, maximum_amount * salary_factor)

    # Em fraude, empurra o valor para fora do comportamento normal.
    if is_fraud:
        amount *= rng.uniform(2.5, 6.5)
        amount = max(amount, account["salary"] * rng.uniform(0.18, 0.65))

    # Arredonda para duas casas como um valor monetario.
    return round(amount, 2)


def _pick_counterparty(account_id: str, all_account_ids: list[str], rng, incoming: bool = False) -> tuple[str, str]:
    # Quando so existe uma conta, usa uma contraparte externa generica.
    if len(all_account_ids) <= 1:
        other_account = "EXTERNAL_ACCOUNT"
    else:
        # Evita que a conta transfira para si mesma.
        other_account = account_id
        while other_account == account_id:
            other_account = rng.choice(all_account_ids)

    # No pix de entrada, a contraparte vira origem e a conta vira destino.
    if incoming:
        return other_account, account_id
    # No restante, a conta vira origem e a contraparte vira destino.
    return account_id, other_account


def _salary_transaction(account: dict[str, Any], current_date, transaction_id: str, rng) -> dict[str, Any]:
    # Deposito de salario costuma ocorrer pela manha.
    timestamp = datetime.combine(
        current_date,
        time(hour=rng.randint(6, 10), minute=rng.randint(0, 59), second=rng.randint(0, 59)),
    )
    # Monta a transacao de salario como credito.
    return {
        "transaction_id": transaction_id,
        "account_id": account["account_id"],
        "timestamp": timestamp,
        "transaction_type": "salary_deposit",
        "amount": round(account["salary"], 2),
        "signed_amount": round(account["salary"], 2),
        "merchant_category": "salary",
        "transaction_channel": "bank_transfer",
        "location": account["home_city"],
        "is_fraud": False,
        "origin_account": "EMPLOYER",
        "destination_account": account["account_id"],
    }


def _incoming_transfer(account: dict[str, Any], current_date, transaction_id: str, all_account_ids: list[str], rng) -> dict[str, Any]:
    # Escolhe a contraparte que enviou o valor.
    origin_account, destination_account = _pick_counterparty(
        account["account_id"],
        all_account_ids,
        rng,
        incoming=True,
    )
    # Sorteia um valor razoavel para recebimento via transferencia.
    amount = round(rng.uniform(35.0, min(account["salary"] * 0.45, 1100.0)), 2)
    # Pix de entrada tende a ocorrer em horario comercial expandido.
    timestamp = random_timestamp(current_date, 7, 22, rng)
    # Monta a transacao de entrada.
    return {
        "transaction_id": transaction_id,
        "account_id": account["account_id"],
        "timestamp": timestamp,
        "transaction_type": "pix_in",
        "amount": amount,
        "signed_amount": amount,
        "merchant_category": "transfer",
        "transaction_channel": "pix",
        "location": account["home_city"],
        "is_fraud": False,
        "origin_account": origin_account,
        "destination_account": destination_account,
    }


def _spending_transaction(
    account: dict[str, Any],
    current_date,
    transaction_id: str,
    all_account_ids: list[str],
    is_fraud: bool,
    rng,
) -> dict[str, Any]:
    # Escolhe a categoria principal do gasto.
    spending_category = _pick_spending_category(account, is_fraud=is_fraud, rng=rng)
    # Escolhe o tipo operacional da transacao.
    transaction_type = _pick_transaction_type(spending_category, is_fraud=is_fraud, rng=rng)
    # Escolhe um canal compativel com o tipo.
    transaction_channel = rng.choice(TYPE_CHANNELS[transaction_type])
    # Comeca tratando a categoria comercial como a categoria de gasto original.
    merchant_category = spending_category

    # Para pix de saida, a categoria comercial vira transferencia.
    if transaction_type == "pix_out":
        merchant_category = "transfer"
    # Para saque, a categoria comercial vira cash_withdrawal.
    elif transaction_type == "atm_withdrawal":
        merchant_category = "cash_withdrawal"

    # Fraudes acontecem em horarios muito menos usuais.
    if is_fraud:
        timestamp = random_timestamp(current_date, 0, 4, rng)
        if rng.random() < 0.35:
            timestamp = random_timestamp(current_date, 22, 23, rng)
    else:
        # Transacoes normais respeitam a janela ativa da conta.
        timestamp = random_timestamp(
            current_date,
            account["active_hour_start"],
            account["active_hour_end"],
            rng,
        )

    # Sorteia o valor financeiro da transacao.
    amount = _pick_amount(account, category=merchant_category, is_fraud=is_fraud, rng=rng)
    # Sorteia a localizacao geografica.
    location = _pick_location(account, is_fraud=is_fraud, rng=rng)

    # Pix de saida usa outra conta como destino.
    if transaction_type == "pix_out":
        origin_account, destination_account = _pick_counterparty(account["account_id"], all_account_ids, rng)
        location = account["home_city"] if not is_fraud else location
    else:
        # Compras e pagamentos usam um destino simbolico de comerciante.
        origin_account = account["account_id"]
        destination_account = f"MERCHANT_{merchant_category.upper()}"

    # Saque em ATM sobrescreve o destino e ajusta a localizacao.
    if merchant_category == "cash_withdrawal":
        destination_account = "ATM_NETWORK"
        location = account["home_city"] if not is_fraud else rng.choice(TRAVEL_CITIES)

    # Pagamento de contas usa um destino institucional fixo.
    if transaction_type == "bill_payment":
        destination_account = "UTILITY_PROVIDER"

    # Retorna a transacao em formato de dicionario.
    return {
        "transaction_id": transaction_id,
        "account_id": account["account_id"],
        "timestamp": timestamp,
        "transaction_type": transaction_type,
        "amount": amount,
        "signed_amount": -amount,
        "merchant_category": merchant_category,
        "transaction_channel": transaction_channel,
        "location": location,
        "is_fraud": bool(is_fraud),
        "origin_account": origin_account,
        "destination_account": destination_account,
    }


def _finalize_candidate(candidate: dict[str, Any], current_balance: float, rng) -> tuple[dict[str, Any] | None, float]:
    # signed_amount guarda o sinal real do impacto no saldo.
    signed_amount = float(candidate.pop("signed_amount"))
    # amount guarda a intensidade monetaria da transacao.
    amount = float(candidate["amount"])

    # Aqui entram apenas transacoes que retiram dinheiro da conta.
    if signed_amount < 0:
        # Se o saldo estiver muito baixo, descarta a transacao em vez de quebrar a consistencia.
        if current_balance <= 20:
            return None, current_balance
        # Se o valor estourar o saldo, reduz o valor para algo plausivel.
        if amount > current_balance:
            amount = round(max(8.0, current_balance * rng.uniform(0.25, 0.95)), 2)
            signed_amount = -amount
            candidate["amount"] = amount

    # Registra o saldo anterior.
    balance_before = round(current_balance, 2)
    # Calcula o saldo posterior.
    balance_after = round(balance_before + signed_amount, 2)

    # Salva o antes e depois dentro da linha de transacao.
    candidate["balance_before"] = balance_before
    candidate["balance_after"] = balance_after
    # Converte o timestamp para texto ISO, o que facilita salvar em CSV.
    candidate["timestamp"] = candidate["timestamp"].isoformat()
    # Converte o rotulo de fraude para inteiro.
    candidate["is_fraud"] = int(candidate["is_fraud"])

    # Retorna a transacao finalizada e o novo saldo corrente.
    return candidate, balance_after


def generate_transactions(
    accounts: list[dict[str, Any]] | pd.DataFrame,
    config: GenerationConfig,
) -> list[dict[str, Any]]:
    # Valida a configuracao da simulacao.
    config.validate()
    # Cria o gerador pseudoaleatorio principal.
    rng = build_rng(config.seed)
    # Normaliza as contas recebidas.
    account_records = _coerce_accounts(accounts)
    # Extrai os identificadores de todas as contas.
    all_account_ids = [account["account_id"] for account in account_records]
    # Descobre o periodo real de simulacao.
    start_date, end_date = config.resolve_dates()

    # Lista onde todas as transacoes geradas serao acumuladas.
    transactions: list[dict[str, Any]] = []
    # Contador sequencial do identificador das transacoes.
    transaction_number = 1

    # Processa cada conta separadamente.
    for account in account_records:
        # Comeca pelo saldo corrente da conta.
        current_balance = float(account["current_balance"])

        # Percorre cada dia do periodo configurado.
        for current_date in date_sequence(start_date, end_date):
            # Guarda as transacoes candidatas daquele dia antes da aplicacao no saldo.
            daily_candidates: list[dict[str, Any]] = []

            # No dia de salario, injeta um deposito.
            if current_date.day == account["salary_day"]:
                transaction_id = f"TX{transaction_number:09d}"
                transaction_number += 1
                daily_candidates.append(_salary_transaction(account, current_date, transaction_id, rng))

            # Com baixa probabilidade, injeta uma transferencia recebida.
            if rng.random() < 0.06:
                transaction_id = f"TX{transaction_number:09d}"
                transaction_number += 1
                daily_candidates.append(
                    _incoming_transfer(account, current_date, transaction_id, all_account_ids, rng),
                )

            # Define quantas transacoes de gasto esse dia tera.
            daily_target = _daily_transactions_target(account, current_date, rng)
            # Define se o dia tera direito a um comportamento anomalo.
            anomaly_budget = 1 if rng.random() < config.fraud_rate else 0

            # Gera o bloco principal de transacoes de gasto.
            for _ in range(daily_target):
                # Se ainda houver orcamento de anomalia, parte das transacoes pode virar fraude.
                is_fraud = anomaly_budget > 0 and rng.random() < 0.55
                transaction_id = f"TX{transaction_number:09d}"
                transaction_number += 1
                daily_candidates.append(
                    _spending_transaction(
                        account,
                        current_date,
                        transaction_id,
                        all_account_ids,
                        is_fraud=is_fraud,
                        rng=rng,
                    ),
                )
                # Consome o orcamento quando uma fraude foi injetada.
                if is_fraud:
                    anomaly_budget -= 1

            # Ordena por horario para aplicar o saldo em ordem cronologica.
            daily_candidates.sort(key=lambda item: item["timestamp"])

            # Finaliza cada transacao e atualiza o saldo da conta.
            for candidate in daily_candidates:
                finalized_candidate, current_balance = _finalize_candidate(candidate, current_balance, rng)
                if finalized_candidate is not None:
                    transactions.append(finalized_candidate)

        # Ao fim da simulacao daquela conta, registra o saldo final obtido.
        account["current_balance"] = round(current_balance, 2)

    # Retorna todas as transacoes geradas.
    return transactions


def transactions_to_frame(transactions: list[dict[str, Any]]) -> pd.DataFrame:
    # Converte a lista de transacoes em DataFrame.
    frame = pd.DataFrame(transactions)
    # Se nao houver linhas, devolve o DataFrame vazio sem ordenar.
    if frame.empty:
        return frame
    # Ordena para manter a leitura cronologica por conta.
    return frame.sort_values(["account_id", "timestamp", "transaction_id"]).reset_index(drop=True)


def validate_transactions(transactions: list[dict[str, Any]] | pd.DataFrame) -> None:
    # Normaliza a entrada para DataFrame.
    transactions_frame = transactions.copy() if isinstance(transactions, pd.DataFrame) else transactions_to_frame(transactions)
    # Nao faz sentido salvar um dataset vazio.
    if transactions_frame.empty:
        msg = "O dataset de transacoes gerado esta vazio."
        raise ValueError(msg)
    # transaction_id deve ser unico.
    if transactions_frame["transaction_id"].duplicated().any():
        msg = "Foram encontrados transaction_id duplicados no dataset de transacoes."
        raise ValueError(msg)
    # Nenhum campo essencial deveria ficar nulo apos a geracao.
    if transactions_frame.isna().sum().sum() > 0:
        msg = "Foram encontrados valores nulos no dataset de transacoes."
        raise ValueError(msg)
    # Valores monetarios precisam ser positivos.
    if (transactions_frame["amount"] <= 0).any():
        msg = "Foram encontrados valores monetarios nao positivos no dataset de transacoes."
        raise ValueError(msg)
    # Saldos finais negativos foram evitados no gerador e nao deveriam aparecer.
    if (transactions_frame["balance_after"] < 0).any():
        msg = "Foram encontrados saldos finais negativos no dataset de transacoes."
        raise ValueError(msg)

    # Contador de quebras na continuidade do saldo.
    continuity_errors = 0
    # Ordena o dataset para validar a sequencia cronologica de cada conta.
    ordered_transactions = transactions_frame.sort_values(["account_id", "timestamp", "transaction_id"])
    # Percorre cada conta separadamente.
    for _, account_group in ordered_transactions.groupby("account_id", sort=False):
        previous_balance_after = None
        for row in account_group.itertuples(index=False):
            # O saldo antes da transacao atual precisa bater com o saldo depois da transacao anterior.
            if previous_balance_after is not None and round(float(row.balance_before), 2) != round(float(previous_balance_after), 2):
                continuity_errors += 1
            previous_balance_after = row.balance_after

    # Interrompe se houver qualquer quebra de continuidade.
    if continuity_errors:
        msg = "Foram encontrados erros de continuidade de saldo entre transacoes sequenciais."
        raise ValueError(msg)


def save_transactions(transactions: list[dict[str, Any]], output_path: Path | None = None) -> Path:
    # Usa o caminho informado ou o padrao do projeto.
    resolved_path = output_path or DEFAULT_TRANSACTIONS_PATH
    # Garante a existencia da pasta de destino.
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    # Salva o CSV sem o indice do DataFrame.
    transactions_to_frame(transactions).to_csv(resolved_path, index=False)
    # Retorna o caminho final salvo.
    return resolved_path
