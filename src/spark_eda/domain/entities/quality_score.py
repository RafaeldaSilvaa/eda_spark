"""Estruturas de pontuação de qualidade dos dados."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.value_objects.severity import Severity


@dataclass(frozen=True)
class QualityFactor:
    """Fator individual de qualidade que compõe uma dimensão.

    Attributes:
        name: Nome descritivo do fator (ex.: "Proporção de nulos", "Cardinalidade").
        score: Pontuação do fator no intervalo [0.0, 1.0].
        internal_weight: Peso do fator dentro de sua dimensão.
        contribution: Contribuição efetiva deste fator para a pontuação da dimensão.
        reason: Explicação textual do motivo desta pontuação.
        severity: Nível de severidade associado ao fator.
        affected_columns: Lista de colunas impactadas por este fator de qualidade.
    """

    name: str
    score: float
    internal_weight: float
    contribution: float
    reason: str
    severity: Severity
    affected_columns: list[str]


@dataclass(frozen=True)
class QualityDimension:
    """Dimensão de qualidade composta por múltiplos fatores.

    Attributes:
        name: Nome da dimensão (ex.: "Completude", "Conformidade", "Unicidade").
        score: Pontuação da dimensão no intervalo [0.0, 100.0].
        weight: Peso da dimensão no cálculo da pontuação geral, em [0.0, 1.0].
        contribution: Contribuição efetiva desta dimensão para a pontuação geral.
        factors: Lista de fatores individuais que compõem esta dimensão.
    """

    name: str
    score: float
    weight: float
    contribution: float
    factors: list[QualityFactor]


@dataclass(frozen=True)
class QualityScore:
    """Pontuação geral de qualidade dos dados.

    Attributes:
        overall: Pontuação geral no intervalo [0.0, 100.0].
        dimensions: Dicionário mapeando nome da dimensão ao seu objeto QualityDimension.
        top_penalizers: Lista dos fatores que mais penalizaram a pontuação geral,
                        ordenados do maior para o menor impacto.
    """

    overall: float
    dimensions: dict[str, QualityDimension]
    top_penalizers: list[QualityFactor]
