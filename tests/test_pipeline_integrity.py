# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# unittest organiza os testes automatizados.
import unittest
# date ajuda a fixar um periodo previsivel de simulacao.
from datetime import date

# Pandas e usado para inspecionar os datasets gerados nos testes.
import pandas as pd

# Importa as configuracoes de geracao e analise.
from src.config import AnalysisConfig, GenerationConfig
# Importa a etapa de criacao de features.
from src.features.feature_engineering import engineer_transaction_features
# Importa a geracao de contas e a sincronizacao de saldo.
from src.generators.account_generator import generate_accounts, sync_account_balances
# Importa a geracao de transacoes.
from src.generators.transaction_generator import generate_transactions
# Importa a etapa de deteccao de anomalias.
from src.models.anomaly_detection import detect_anomalies


class PipelineIntegrityTests(unittest.TestCase):
    def test_account_current_balance_matches_last_transaction_balance(self) -> None:
        # Cria uma configuracao pequena e deterministica para o teste.
        config = GenerationConfig(
            accounts_count=5,
            months=1,
            fraud_rate=0.2,
            seed=11,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 15),
        )
        # Gera contas sinteticas.
        accounts = generate_accounts(config.accounts_count, seed=config.seed)
        # Gera as transacoes dessas contas.
        transactions = generate_transactions(accounts, config)
        # Sincroniza o saldo final das contas com a ultima transacao registrada.
        sync_account_balances(accounts, transactions)

        # Converte a lista de transacoes em DataFrame para facilitar a comparacao.
        transactions_frame = pd.DataFrame(transactions)
        # Recupera o ultimo saldo observado por conta.
        final_balances = (
            transactions_frame.sort_values(["account_id", "timestamp"])
            .groupby("account_id")["balance_after"]
            .last()
            .to_dict()
        )

        # Verifica se o current_balance de cada conta bate com o ultimo balance_after.
        for account in accounts:
            self.assertAlmostEqual(
                account["current_balance"],
                final_balances[account["account_id"]],
                places=2,
            )

    def test_pix_out_uses_transfer_category(self) -> None:
        # Cria uma configuracao pequena para inspecionar a consistencia do tipo pix_out.
        config = GenerationConfig(
            accounts_count=8,
            months=1,
            fraud_rate=0.3,
            seed=21,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
        # Gera contas para o teste.
        accounts = generate_accounts(config.accounts_count, seed=config.seed)
        # Gera transacoes e converte para DataFrame.
        transactions = pd.DataFrame(generate_transactions(accounts, config))

        # Filtra apenas as transacoes pix_out.
        pix_out_transactions = transactions.loc[transactions["transaction_type"] == "pix_out"]
        # Confirma que o dataset realmente gerou esse tipo de transacao.
        self.assertFalse(pix_out_transactions.empty)
        # Confirma que todas elas usam a categoria comercial transfer.
        self.assertTrue((pix_out_transactions["merchant_category"] == "transfer").all())

    def test_anomaly_detection_handles_small_dataset(self) -> None:
        # Monta manualmente um dataset minimo com uma unica transacao.
        transactions = pd.DataFrame(
            [
                {
                    "transaction_id": "TX000000001",
                    "account_id": "A00001",
                    "timestamp": "2026-01-01T10:00:00",
                    "transaction_type": "salary_deposit",
                    "amount": 2500.0,
                    "balance_before": 100.0,
                    "balance_after": 2600.0,
                    "merchant_category": "salary",
                    "transaction_channel": "bank_transfer",
                    "location": "Aracaju",
                    "is_fraud": 0,
                    "origin_account": "EMPLOYER",
                    "destination_account": "A00001",
                },
            ],
        )
        # Converte o timestamp para datetime.
        transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])

        # Gera as features do dataset minimo.
        enriched_transactions, feature_matrix = engineer_transaction_features(transactions)
        # Executa o detector para conferir se ele nao quebra com poucos dados.
        scored_transactions, model = detect_anomalies(
            enriched_transactions,
            feature_matrix,
            AnalysisConfig(contamination=0.1, top_n=5, random_state=42),
        )

        # Como o dataset e minimo, o modelo nao precisa ser treinado.
        self.assertIsNone(model)
        # E nenhuma linha deve ser marcada como anomalia por seguranca.
        self.assertTrue((scored_transactions["is_anomaly"] == 0).all())


if __name__ == "__main__":
    # Executa os testes quando o arquivo e chamado diretamente.
    unittest.main()
