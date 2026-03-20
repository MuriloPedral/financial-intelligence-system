from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.config import AnalysisConfig


def detect_anomalies(
    enriched_transactions: pd.DataFrame,
    feature_matrix: pd.DataFrame,
    config: AnalysisConfig,
) -> tuple[pd.DataFrame, IsolationForest | None]:
    config.validate()
    if enriched_transactions.empty or feature_matrix.empty:
        msg = "Pelo menos uma transacao e necessaria para executar a deteccao de anomalias."
        raise ValueError(msg)

    scorable_mask = enriched_transactions["transaction_type"] != "salary_deposit"
    if not scorable_mask.any():
        scorable_mask = pd.Series(True, index=enriched_transactions.index)

    scorable_features = feature_matrix.loc[scorable_mask]
    if len(scorable_features) < 2:
        scored_transactions = enriched_transactions.copy()
        scored_transactions["anomaly_score"] = 0.0
        scored_transactions["raw_anomaly_score"] = 0.0
        scored_transactions["is_anomaly"] = 0
        return scored_transactions, None

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(scorable_features)
    model = IsolationForest(
        contamination=config.contamination,
        n_estimators=300,
        random_state=config.random_state,
    )

    predictions = model.fit_predict(scaled_features)
    raw_scores = -model.decision_function(scaled_features)
    score_min = float(np.min(raw_scores))
    score_max = float(np.max(raw_scores))
    if score_max == score_min:
        normalized_scores = np.zeros_like(raw_scores)
    else:
        normalized_scores = (raw_scores - score_min) / (score_max - score_min)

    scored_transactions = enriched_transactions.copy()
    scored_transactions["anomaly_score"] = 0.0
    scored_transactions["raw_anomaly_score"] = 0.0
    scored_transactions["is_anomaly"] = 0
    scored_transactions.loc[scorable_mask, "anomaly_score"] = normalized_scores.round(4)
    scored_transactions.loc[scorable_mask, "raw_anomaly_score"] = raw_scores.round(6)
    scored_transactions.loc[scorable_mask, "is_anomaly"] = (predictions == -1).astype(int)
    scored_transactions = scored_transactions.sort_values(
        ["is_anomaly", "anomaly_score", "timestamp"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    return scored_transactions, model
