"""Modelos de dados para integração com OmniRoute AI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AiCommentary:
    """Comentários gerados por IA para cada seção do relatório EDA.

    Attributes:
        overview: Comentário sobre a visão geral do dataset.
        schema: Comentário sobre o esquema e tipos de colunas.
        quality: Comentário sobre a qualidade dos dados.
        stats: Comentário sobre estatísticas descritivas.
        distributions: Comentário sobre distribuições de valores.
        correlations: Comentário sobre correlações entre colunas.
        outliers: Comentário sobre detecção de outliers.
        insights: Comentário sobre insights gerados.
        recommendations: Comentário sobre recomendações de ação.
        executive_analysis: Análise executiva transversal identificando
            padrões e implicações de negócio.
    """

    overview: str | None = None
    schema: str | None = None
    quality: str | None = None
    stats: str | None = None
    distributions: str | None = None
    correlations: str | None = None
    outliers: str | None = None
    insights: str | None = None
    recommendations: str | None = None
    executive_analysis: str | None = None


class OmniRouteError(Exception):
    """Erro levantado quando uma operação OmniRoute falha."""
