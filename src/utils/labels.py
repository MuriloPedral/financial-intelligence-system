from __future__ import annotations


TRANSACTION_TYPE_LABELS_PT = {
    "salary_deposit": "deposito de salario",
    "pix_in": "pix recebido",
    "pix_out": "pix enviado",
    "card_purchase": "compra com cartao",
    "online_purchase": "compra online",
    "bill_payment": "pagamento de contas",
    "atm_withdrawal": "saque em caixa eletronico",
}

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
    return TRANSACTION_TYPE_LABELS_PT.get(transaction_type, transaction_type.replace("_", " "))


def humanize_category(category: str) -> str:
    return CATEGORY_LABELS_PT.get(category, category.replace("_", " "))
