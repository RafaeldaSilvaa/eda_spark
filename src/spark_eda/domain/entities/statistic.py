"""Estatísticas descritivas agrupadas por tipo de coluna."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumericStats:
    """Estatísticas descritivas para colunas numéricas (int, long, double, decimal).

    Attributes:
        mean: Média aritmética dos valores.
        std: Desvio padrão dos valores.
        min: Valor mínimo observado.
        q25: Primeiro quartil (percentil 25).
        q50: Mediana (percentil 50).
        q75: Terceiro quartil (percentil 75).
        max: Valor máximo observado.
        skewness: Assimetria da distribuição.
        kurtosis: Curtose da distribuição.
    """

    mean: float
    std: float
    min: float
    q25: float
    q50: float
    q75: float
    max: float
    skewness: float
    kurtosis: float


@dataclass(frozen=True)
class CategoricalStats:
    """Estatísticas descritivas para colunas categóricas (string, boolean como categorias).

    Attributes:
        value_counts: Dicionário com a contagem de cada valor distinto.
        mode: Valor mais frequente (moda), ou None se indisponível.
        cardinality: Número de valores distintos na coluna.
        unique_ratio: Proporção de valores únicos em relação ao total.
    """

    value_counts: dict[str, int]
    mode: str | None
    cardinality: int
    unique_ratio: float


@dataclass(frozen=True)
class TemporalStats:
    """Estatísticas descritivas para colunas temporais (date, timestamp).

    Attributes:
        min_date: Data mais antiga observada no formato ISO (YYYY-MM-DD).
        max_date: Data mais recente observada no formato ISO (YYYY-MM-DD).
        range_days: Número de dias entre a data mínima e máxima.
        gap_count: Número de lacunas temporais identificadas na série.
    """

    min_date: str
    max_date: str
    range_days: int
    gap_count: int


@dataclass(frozen=True)
class TextStats:
    """Estatísticas descritivas para colunas textuais (strings longas).

    Attributes:
        min_length: Comprimento mínimo observado entre os valores.
        max_length: Comprimento máximo observado entre os valores.
        avg_length: Comprimento médio dos valores.
        empty_ratio: Proporção de valores vazios ou somente espaços em branco.
    """

    min_length: int
    max_length: int
    avg_length: float
    empty_ratio: float


@dataclass(frozen=True)
class BooleanStats:
    """Estatísticas descritivas para colunas booleanas.

    Attributes:
        true_count: Número de valores verdadeiros (true).
        false_count: Número de valores falsos (false).
        true_ratio: Proporção de valores verdadeiros em relação ao total.
    """

    true_count: int
    false_count: int
    true_ratio: float


type Statistic = NumericStats | CategoricalStats | TemporalStats | TextStats | BooleanStats
"""Tipo união que representa qualquer conjunto de estatísticas de coluna."""
