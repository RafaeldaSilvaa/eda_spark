"""Recomendações de ação geradas pela análise."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.value_objects.recommendation_category import RecommendationCategory


@dataclass(frozen=True)
class Recommendation:
    """Recomendação de ação gerada a partir da análise exploratória.

    Attributes:
        category: Categoria temática da recomendação.
        priority: Prioridade da recomendação em uma escala de 1 (mais urgente) a 5 (menos urgente).
        column: Nome da coluna associada à recomendação, ou None se global.
        message: Descrição textual do problema identificado.
        action: Descrição textual da ação recomendada para resolver o problema.
    """

    category: RecommendationCategory
    priority: int
    column: str | None
    message: str
    action: str
