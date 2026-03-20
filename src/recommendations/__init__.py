# Reexporta a funcao principal para facilitar o uso no pipeline.
from src.recommendations.financial_recommendations import build_financial_recommendations

__all__ = ["build_financial_recommendations"]
