# Reexporta a funcao principal para facilitar o uso no pipeline.
from src.explainability.anomaly_explainer import explain_anomalies

__all__ = ["explain_anomalies"]
