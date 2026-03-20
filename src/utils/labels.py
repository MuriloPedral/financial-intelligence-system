# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations


# Traduz os tipos tecnicos de transacao para uma descricao mais natural.
TRANSACTION_TYPE_LABELS_PT = {
    "salary_deposit": "deposito de salario",
    "pix_in": "pix recebido",
    "pix_out": "pix enviado",
    "card_purchase": "compra com cartao",
    "online_purchase": "compra online",
    "bill_payment": "pagamento de contas",
    "atm_withdrawal": "saque em caixa eletronico",
}

# Traduz as categorias de gasto para textos usados em explicacoes e recomendacoes.
CATEGORY_LABELS_PT = {
    "salary": "salario",
    "transfer": "transferencias",
    "groceries": "mercado",
    "restaurant": "alimentacao fora de casa",
    "transport": "transporte",
    "entertainment": "entretenimento",
    "utilities": "contas recorrentes",
    "health": "saude",
    "shopping": "compras",
    "travel": "viagens",
    "cash_withdrawal": "saques",
}


def humanize_transaction_type(transaction_type: str) -> str:
    # Usa a traducao conhecida ou devolve o proprio valor tecnico como fallback.
    return TRANSACTION_TYPE_LABELS_PT.get(transaction_type, transaction_type.replace("_", " "))


def humanize_category(category: str) -> str:
    # Usa a traducao conhecida ou devolve o proprio valor tecnico como fallback.
    return CATEGORY_LABELS_PT.get(category, category.replace("_", " "))
