"""Insights gerados durante a análise exploratória."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.severity import Severity


@dataclass(frozen=True)
class Insight:
    """Insight ou descoberta gerado durante a análise exploratória de dados.

    Attributes:
        category: Categoria temática do insight.
        severity: Nível de severidade atribuído ao insight.
        column: Nome da coluna associada ao insight, ou None se global.
        message: Descrição textual do insight em linguagem natural.
        metric_value: Valor numérico que suporta o insight, quando aplicável.
    """

    category: InsightCategory
    severity: Severity
    column: str | None
    message: str
    metric_value: float | None
