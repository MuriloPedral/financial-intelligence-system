from __future__ import annotations

from collections.abc import Mapping, Sequence
from random import Random
from typing import TypeVar


T = TypeVar("T")


def build_rng(seed: int | None = None) -> Random:
    return Random(seed)


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    total = float(sum(weights.values()))
    if total <= 0:
        uniform_weight = 1.0 / max(len(weights), 1)
        return {key: uniform_weight for key in weights}
    return {key: value / total for key, value in weights.items()}


def choose_weighted(options: Mapping[T, float], rng: Random) -> T:
    normalized = normalize_weights(options)
    items = list(normalized.keys())
    weights = list(normalized.values())
    return rng.choices(items, weights=weights, k=1)[0]


def sample_without_replacement(options: Sequence[T], sample_size: int, rng: Random) -> list[T]:
    capped_size = max(0, min(sample_size, len(options)))
    return rng.sample(list(options), k=capped_size)
