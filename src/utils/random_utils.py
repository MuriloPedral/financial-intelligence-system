# Permite usar anotacoes de tipo modernas sem resolver tudo imediatamente.
from __future__ import annotations

# Tipos auxiliares para declarar mapeamentos e sequencias.
from collections.abc import Mapping, Sequence
# Random oferece um gerador pseudoaleatorio controlado por semente.
from random import Random
# TypeVar deixa as funcoes genericas para qualquer tipo de item.
from typing import TypeVar


# T representa qualquer tipo de valor sorteavel.
T = TypeVar("T")


def build_rng(seed: int | None = None) -> Random:
    # Cria um gerador pseudoaleatorio local para evitar depender do estado global.
    return Random(seed)


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    # Soma todos os pesos recebidos.
    total = float(sum(weights.values()))
    # Se a soma for invalida, distribui pesos uniformes.
    if total <= 0:
        uniform_weight = 1.0 / max(len(weights), 1)
        return {key: uniform_weight for key in weights}
    # Caso contrario, normaliza cada peso para a soma final ser 1.
    return {key: value / total for key, value in weights.items()}


def choose_weighted(options: Mapping[T, float], rng: Random) -> T:
    # Garante que os pesos estejam normalizados.
    normalized = normalize_weights(options)
    # Separa os itens e os pesos em listas paralelas.
    items = list(normalized.keys())
    weights = list(normalized.values())
    # Sorteia exatamente um item respeitando os pesos informados.
    return rng.choices(items, weights=weights, k=1)[0]


def sample_without_replacement(options: Sequence[T], sample_size: int, rng: Random) -> list[T]:
    # Garante que o tamanho amostral fique dentro do limite da sequencia.
    capped_size = max(0, min(sample_size, len(options)))
    # Sorteia sem repeticao.
    return rng.sample(list(options), k=capped_size)
