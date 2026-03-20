from __future__ import annotations

import unittest
from datetime import date

import pandas as pd

from src.config import AnalysisConfig, GenerationConfig
from src.explainability.anomaly_explainer import explain_anomalies
from src.features.feature_engineering import engineer_transaction_features
from src.generators.account_generator import generate_accounts, sync_account_balances
from src.generators.transaction_generator import generate_transactions
from src.models.anomaly_detection import detect_anomalies
from src.profiles.account_profiles import build_account_profiles
from src.recommendations.financial_recommendations import build_financial_recommendations
from src.reporting.report_generator import build_anomaly_report_frame, build_recommendations_report_frame


class PipelineIntegrityTests(unittest.TestCase):
    def test_anomaly_report_frame_exports_only_detected_anomalies(self) -> None:
        scored_transactions = pd.DataFrame(
            [
                {
                    "transaction_id": "TX000000001",
                    "account_id": "A00001",
                    "timestamp": "2026-01-01T10:00:00",
                    "transaction_type": "card_purchase",
                    "merchant_category": "groceries",
                    "transaction_channel": "debit_card",
                    "location": "Aracaju",
                    "amount": 80.0,
                    "balance_before": 1000.0,
                    "balance_after": 920.0,
                    "anomaly_score": 0.10,
                    "raw_anomaly_score": 0.01,
                    "anomaly_explanation": "",
                    "explanation_count": 0,
                    "is_anomaly": 0,
                },
                {
                    "transaction_id": "TX000000002",
                    "account_id": "A00001",
                    "timestamp": "2026-01-02T02:00:00",
                    "transaction_type": "online_purchase",
                    "merchant_category": "travel",
                    "transaction_channel": "internet_banking",
                    "location": "Sao Paulo",
                    "amount": 900.0,
                    "balance_before": 920.0,
                    "balance_after": 20.0,
                    "anomaly_score": 0.99,
                    "raw_anomaly_score": 0.91,
                    "anomaly_explanation": "Valor muito acima da media.",
                    "explanation_count": 1,
                    "is_anomaly": 1,
                },
            ],
        )

        anomaly_report = build_anomaly_report_frame(scored_transactions)

        self.assertEqual(len(anomaly_report), 1)
        self.assertEqual(anomaly_report.iloc[0]["transaction_id"], "TX000000002")
        self.assertIn("anomaly_rank", anomaly_report.columns)

    def test_account_profiles_capture_financial_behavior(self) -> None:
        transactions = pd.DataFrame(
            [
                {
                    "transaction_id": "TX000000001",
                    "account_id": "A00001",
                    "timestamp": "2026-01-05T09:00:00",
                    "transaction_type": "salary_deposit",
                    "amount": 3200.0,
                    "balance_before": 200.0,
                    "balance_after": 3400.0,
                    "merchant_category": "salary",
                    "transaction_channel": "bank_transfer",
                    "location": "Aracaju",
                    "origin_account": "EMPLOYER",
                    "destination_account": "A00001",
                },
                {
                    "transaction_id": "TX000000002",
                    "account_id": "A00001",
                    "timestamp": "2026-01-05T12:20:00",
                    "transaction_type": "card_purchase",
                    "amount": 180.0,
                    "balance_before": 3400.0,
                    "balance_after": 3220.0,
                    "merchant_category": "groceries",
                    "transaction_channel": "debit_card",
                    "location": "Aracaju",
                    "origin_account": "A00001",
                    "destination_account": "MERCHANT_GROCERIES",
                },
                {
                    "transaction_id": "TX000000003",
                    "account_id": "A00001",
                    "timestamp": "2026-01-06T13:10:00",
                    "transaction_type": "card_purchase",
                    "amount": 95.0,
                    "balance_before": 3220.0,
                    "balance_after": 3125.0,
                    "merchant_category": "restaurant",
                    "transaction_channel": "credit_card",
                    "location": "Aracaju",
                    "origin_account": "A00001",
                    "destination_account": "MERCHANT_RESTAURANT",
                },
                {
                    "transaction_id": "TX000000004",
                    "account_id": "A00001",
                    "timestamp": "2026-01-07T10:40:00",
                    "transaction_type": "bill_payment",
                    "amount": 220.0,
                    "balance_before": 3125.0,
                    "balance_after": 2905.0,
                    "merchant_category": "utilities",
                    "transaction_channel": "mobile_app",
                    "location": "Aracaju",
                    "origin_account": "A00001",
                    "destination_account": "UTILITY_PROVIDER",
                },
            ],
        )
        transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])

        profiles = build_account_profiles(transactions)
        profile = profiles.iloc[0]

        self.assertEqual(len(profiles), 1)
        self.assertEqual(profile["transaction_count"], 4)
        self.assertEqual(profile["estimated_monthly_income"], 3200.0)
        self.assertEqual(profile["most_common_transaction_type"], "card_purchase")
        self.assertIn("utilities", profile["spending_category_amount_share"])

    def test_account_current_balance_matches_last_transaction_balance(self) -> None:
        config = GenerationConfig(
            accounts_count=5,
            months=1,
            fraud_rate=0.2,
            seed=11,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 15),
        )
        accounts = generate_accounts(config.accounts_count, seed=config.seed)
        transactions = generate_transactions(accounts, config)
        sync_account_balances(accounts, transactions)

        transactions_frame = pd.DataFrame(transactions)
        final_balances = (
            transactions_frame.sort_values(["account_id", "timestamp"])
            .groupby("account_id")["balance_after"]
            .last()
            .to_dict()
        )

        for account in accounts:
            self.assertAlmostEqual(
                account["current_balance"],
                final_balances[account["account_id"]],
                places=2,
            )

    def test_pix_out_uses_transfer_category(self) -> None:
        config = GenerationConfig(
            accounts_count=8,
            months=1,
            fraud_rate=0.3,
            seed=21,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
        accounts = generate_accounts(config.accounts_count, seed=config.seed)
        transactions = pd.DataFrame(generate_transactions(accounts, config))

        pix_out_transactions = transactions.loc[transactions["transaction_type"] == "pix_out"]
        self.assertFalse(pix_out_transactions.empty)
        self.assertTrue((pix_out_transactions["merchant_category"] == "transfer").all())

    def test_anomaly_detection_handles_small_dataset(self) -> None:
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
        transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])

        enriched_transactions, feature_matrix = engineer_transaction_features(transactions)
        scored_transactions, model = detect_anomalies(
            enriched_transactions,
            feature_matrix,
            AnalysisConfig(contamination=0.1, top_n=5, random_state=42),
        )

        self.assertIsNone(model)
        self.assertTrue((scored_transactions["is_anomaly"] == 0).all())

    def test_anomaly_explanations_compare_transaction_with_profile(self) -> None:
        historical_transactions = pd.DataFrame(
            [
                {
                    "transaction_id": "TX000000010",
                    "account_id": "A00002",
                    "timestamp": "2026-01-01T12:00:00",
                    "transaction_type": "card_purchase",
                    "amount": 100.0,
                    "balance_before": 2500.0,
                    "balance_after": 2400.0,
                    "merchant_category": "groceries",
                    "transaction_channel": "debit_card",
                    "location": "Aracaju",
                    "origin_account": "A00002",
                    "destination_account": "MERCHANT_GROCERIES",
                },
                {
                    "transaction_id": "TX000000011",
                    "account_id": "A00002",
                    "timestamp": "2026-01-03T12:30:00",
                    "transaction_type": "card_purchase",
                    "amount": 110.0,
                    "balance_before": 2400.0,
                    "balance_after": 2290.0,
                    "merchant_category": "groceries",
                    "transaction_channel": "debit_card",
                    "location": "Aracaju",
                    "origin_account": "A00002",
                    "destination_account": "MERCHANT_GROCERIES",
                },
                {
                    "transaction_id": "TX000000012",
                    "account_id": "A00002",
                    "timestamp": "2026-01-05T13:10:00",
                    "transaction_type": "card_purchase",
                    "amount": 92.0,
                    "balance_before": 2290.0,
                    "balance_after": 2198.0,
                    "merchant_category": "groceries",
                    "transaction_channel": "credit_card",
                    "location": "Aracaju",
                    "origin_account": "A00002",
                    "destination_account": "MERCHANT_GROCERIES",
                },
            ],
        )
        anomalous_transaction = pd.DataFrame(
            [
                {
                    "transaction_id": "TX000000013",
                    "account_id": "A00002",
                    "timestamp": "2026-01-06T02:15:00",
                    "transaction_type": "online_purchase",
                    "amount": 680.0,
                    "balance_before": 2198.0,
                    "balance_after": 1518.0,
                    "merchant_category": "travel",
                    "transaction_channel": "internet_banking",
                    "location": "Sao Paulo",
                    "origin_account": "A00002",
                    "destination_account": "MERCHANT_TRAVEL",
                },
            ],
        )

        historical_transactions["timestamp"] = pd.to_datetime(historical_transactions["timestamp"])
        anomalous_transaction["timestamp"] = pd.to_datetime(anomalous_transaction["timestamp"])
        full_transactions = pd.concat([historical_transactions, anomalous_transaction], ignore_index=True)

        enriched_transactions, _ = engineer_transaction_features(full_transactions)
        account_profiles = build_account_profiles(historical_transactions)

        scored_transactions = enriched_transactions.copy()
        scored_transactions["anomaly_score"] = 0.0
        scored_transactions["raw_anomaly_score"] = 0.0
        scored_transactions["is_anomaly"] = 0
        scored_transactions.loc[
            scored_transactions["transaction_id"] == "TX000000013",
            ["anomaly_score", "raw_anomaly_score", "is_anomaly"],
        ] = [0.99, 1.25, 1]

        explained_transactions = explain_anomalies(scored_transactions, account_profiles)
        anomaly_row = explained_transactions.loc[
            explained_transactions["transaction_id"] == "TX000000013"
        ].iloc[0]

        self.assertGreaterEqual(anomaly_row["explanation_count"], 2)
        self.assertIn("Valor da transacao", anomaly_row["anomaly_explanation"])
        self.assertIn("horario incomum", anomaly_row["anomaly_explanation"])

    def test_financial_recommendations_reflect_account_spending_pattern(self) -> None:
        profiles = pd.DataFrame(
            [
                {
                    "account_id": "A00003",
                    "spending_category_amount_share": {
                        "restaurant": 0.45,
                        "entertainment": 0.25,
                        "shopping": 0.12,
                        "groceries": 0.10,
                        "utilities": 0.08,
                    },
                    "category_diversity": 5,
                    "impulsive_spending_share": 0.82,
                    "estimated_monthly_income": 3000.0,
                    "average_monthly_spend": 3150.0,
                    "spend_to_income_ratio": 1.05,
                },
            ],
        )

        recommendations = build_financial_recommendations(profiles)
        recommendation_row = recommendations.iloc[0]

        self.assertGreaterEqual(recommendation_row["recommendation_count"], 3)
        self.assertIn("45%", recommendation_row["recommendations_text"])
        self.assertIn("despesas impulsivas", recommendation_row["recommendations_text"])
        self.assertIn("renda estimada", recommendation_row["recommendations_text"])

    def test_recommendation_report_frame_filters_non_actionable_rows(self) -> None:
        recommendations = pd.DataFrame(
            [
                {
                    "account_id": "A00010",
                    "top_spending_category": "travel",
                    "top_spending_share": 0.62,
                    "estimated_monthly_income": 3000.0,
                    "average_monthly_spend": 3600.0,
                    "spend_to_income_ratio": 1.20,
                    "impulsive_spending_share": 0.45,
                    "recommendations": ["Teste 1", "Teste 2"],
                    "recommendations_text": "Teste 1 | Teste 2",
                    "recommendation_count": 2,
                    "actionable_recommendation_count": 2,
                    "has_actionable_recommendation": 1,
                    "recommendation_priority": 5.0,
                },
                {
                    "account_id": "A00011",
                    "top_spending_category": "groceries",
                    "top_spending_share": 0.20,
                    "estimated_monthly_income": 3000.0,
                    "average_monthly_spend": 1800.0,
                    "spend_to_income_ratio": 0.60,
                    "impulsive_spending_share": 0.10,
                    "recommendations": ["Seu padrao financeiro parece equilibrado."],
                    "recommendations_text": "Seu padrao financeiro parece equilibrado.",
                    "recommendation_count": 1,
                    "actionable_recommendation_count": 0,
                    "has_actionable_recommendation": 0,
                    "recommendation_priority": 0.0,
                },
            ],
        )

        recommendation_report = build_recommendations_report_frame(recommendations)

        self.assertEqual(len(recommendation_report), 1)
        self.assertEqual(recommendation_report.iloc[0]["account_id"], "A00010")
        self.assertNotIn("recommendations", recommendation_report.columns)


if __name__ == "__main__":
    unittest.main()
