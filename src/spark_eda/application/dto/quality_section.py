"""DTO da seção de qualidade dos dados."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityFactorReport:
    """Fator de qualidade na apresentação do relatório.

    Attributes:
        name: Nome descritivo do fator.
        score: Pontuação do fator no intervalo ``[0.0, 1.0]``.
        reason: Explicação textual para a pontuação atribuída.
        severity: Nível de severidade (``"low"``, ``"medium"``, ``"high"``, ``"critical"``).
        affected_columns: Lista de colunas impactadas.
    """

    name: str
    score: float
    reason: str
    severity: str
    affected_columns: list[str]


@dataclass(frozen=True)
class QualityDimensionReport:
    """Dimensão de qualidade na apresentação do relatório.

    Attributes:
        name: Nome da dimensão.
        score: Pontuação da dimensão no intervalo ``[0.0, 100.0]``.
        weight: Peso da dimensão na pontuação geral.
        factors: Lista de fatores que compõem a dimensão.
    """

    name: str
    score: float
    weight: float
    factors: list[QualityFactorReport]


@dataclass(frozen=True)
class QualityReport:
    """Relatório de qualidade dos dados.

    Attributes:
        overall: Pontuação geral no intervalo ``[0.0, 100.0]``.
        dimensions: Lista de dimensões de qualidade avaliadas.
        top_penalizers: Lista dos fatores mais penalizadores.
    """

    overall: float
    dimensions: list[QualityDimensionReport]
    top_penalizers: list[QualityFactorReport]
