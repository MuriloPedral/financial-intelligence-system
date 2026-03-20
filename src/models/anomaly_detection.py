# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Numpy e Pandas apoiam o calculo dos scores.
import numpy as np
import pandas as pd
# Isolation Forest sera o algoritmo principal de deteccao.
from sklearn.ensemble import IsolationForest
# StandardScaler coloca as features na mesma escala.
from sklearn.preprocessing import StandardScaler

# Importa a configuracao do modelo.
from src.config import AnalysisConfig


def detect_anomalies(
    enriched_transactions: pd.DataFrame,
    feature_matrix: pd.DataFrame,
    config: AnalysisConfig,
) -> tuple[pd.DataFrame, IsolationForest | None]:
    # Valida os parametros do modelo.
    config.validate()
    # O modelo precisa de pelo menos uma linha para funcionar.
    if enriched_transactions.empty or feature_matrix.empty:
        msg = "Pelo menos uma transacao e necessaria para executar a deteccao de anomalias."
        raise ValueError(msg)

    # Depositos de salario tendem a ser altos, mas nao sao o foco principal do score.
    scorable_mask = enriched_transactions["transaction_type"] != "salary_deposit"
    # Se so existirem salarios, libera todo o dataset para evitar filtro vazio.
    if not scorable_mask.any():
        scorable_mask = pd.Series(True, index=enriched_transactions.index)

    # Separa apenas as linhas que entrarao no calculo do score.
    scorable_features = feature_matrix.loc[scorable_mask]
    # Para datasets minimos, devolve score zero sem tentar treinar um modelo instavel.
    if len(scorable_features) < 2:
        scored_transactions = enriched_transactions.copy()
        scored_transactions["anomaly_score"] = 0.0
        scored_transactions["raw_anomaly_score"] = 0.0
        scored_transactions["is_anomaly"] = 0
        return scored_transactions, None

    # Padroniza as colunas para que nenhuma domine a analise apenas por escala.
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(scorable_features)

    # Cria o Isolation Forest com bastante arvores para um score mais estavel.
    model = IsolationForest(
        contamination=config.contamination,
        n_estimators=300,
        random_state=config.random_state,
    )

    # Ajusta o modelo e devolve a classificacao das linhas analisadas.
    predictions = model.fit_predict(scaled_features)
    # Inverte o sinal para que scores maiores representem maior anomalia.
    raw_scores = -model.decision_function(scaled_features)

    # Descobre a faixa de valores dos scores crus.
    score_min = float(np.min(raw_scores))
    score_max = float(np.max(raw_scores))
    # Evita divisao por zero se todos os scores forem iguais.
    if score_max == score_min:
        normalized_scores = np.zeros_like(raw_scores)
    else:
        # Normaliza para uma faixa de 0 a 1, mais intuitiva para leitura.
        normalized_scores = (raw_scores - score_min) / (score_max - score_min)

    # Copia o dataset original para anexar os resultados da modelagem.
    scored_transactions = enriched_transactions.copy()
    # Inicializa as colunas de saida.
    scored_transactions["anomaly_score"] = 0.0
    scored_transactions["raw_anomaly_score"] = 0.0
    scored_transactions["is_anomaly"] = 0
    # Preenche score e classificacao apenas nas linhas pontuadas pelo modelo.
    scored_transactions.loc[scorable_mask, "anomaly_score"] = normalized_scores.round(4)
    scored_transactions.loc[scorable_mask, "raw_anomaly_score"] = raw_scores.round(6)
    scored_transactions.loc[scorable_mask, "is_anomaly"] = (predictions == -1).astype(int)
    # Ordena para colocar as anomalias mais fortes primeiro.
    scored_transactions = scored_transactions.sort_values(
        ["is_anomaly", "anomaly_score", "timestamp"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    # Retorna tanto o dataset pontuado quanto o modelo treinado.
    return scored_transactions, model
