"""Estruturas de distribuição de valores agrupadas por tipo de coluna."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumericDistribution:
    """Distribuição dos valores de uma coluna numérica em intervalos (bins).

    Attributes:
        bins: Lista de tuplas representando cada intervalo da distribuição.
              Cada tupla contém (limite_inferior, limite_superior, contagem).
    """

    bins: list[tuple[float, float, int]]


@dataclass(frozen=True)
class CategoricalDistribution:
    """Distribuição dos valores de uma coluna categórica por categoria.

    Attributes:
        categories: Lista de tuplas (categoria, contagem) ordenadas por frequência.
        others_count: Contagem agregada de categorias com frequência muito baixa.
    """

    categories: list[tuple[str, int]]
    others_count: int


@dataclass(frozen=True)
class TemporalDistribution:
    """Distribuição dos valores de uma coluna temporal por período.

    Attributes:
        periods: Lista de tuplas (rótulo_do_período, contagem) representando
                 a série temporal agregada.
    """

    periods: list[tuple[str, int]]


type Distribution = NumericDistribution | CategoricalDistribution | TemporalDistribution
"""Tipo união que representa qualquer distribuição de coluna."""
