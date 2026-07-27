"""Presenter que converte QualityScore em QualityReport."""

from __future__ import annotations

from typing import Any

from spark_eda.application.dto.quality_section import (
    QualityDimensionReport,
    QualityFactorReport,
    QualityReport,
)
from spark_eda.application.ports.output_presenter import OutputPresenter
from spark_eda.domain.entities.quality_score import QualityScore


class QualityPresenter(OutputPresenter):
    """Presenter que converte um ``QualityScore`` em um ``QualityReport``.

    Traduz entidades de qualidade do domínio (``QualityScore``,
    ``QualityDimension``, ``QualityFactor``) em DTOs de apresentação
    (``QualityReport``, ``QualityDimensionReport``, ``QualityFactorReport``).
    """

    def present(self, quality: QualityScore) -> QualityReport:
        """Converte uma pontuação de qualidade em um ``QualityReport``.

        Args:
            quality: Pontuação de qualidade com dimensões e fatores.

        Returns:
            ``QualityReport`` pronto para renderização.
        """
        dimensions: list[QualityDimensionReport] = [
            QualityDimensionReport(
                name=dim.name,
                score=dim.score,
                weight=dim.weight,
                factors=[
                    QualityFactorReport(
                        name=factor.name,
                        score=factor.score,
                        reason=factor.reason,
                        severity=factor.severity.value,
                        affected_columns=factor.affected_columns,
                    )
                    for factor in dim.factors
                ],
            )
            for dim in quality.dimensions.values()
        ]

        top_penalizers: list[QualityFactorReport] = [
            QualityFactorReport(
                name=factor.name,
                score=factor.score,
                reason=factor.reason,
                severity=factor.severity.value,
                affected_columns=factor.affected_columns,
            )
            for factor in quality.top_penalizers
        ]

        return QualityReport(
            overall=quality.overall,
            dimensions=dimensions,
            top_penalizers=top_penalizers,
        )

    def present_analysis(self, analysis: Any) -> Any:
        """Implementa o contrato ``OutputPresenter.present_analysis``.

        Args:
            analysis: Análise exploratória (não usada neste presenter).

        Raises:
            NotImplementedError: Sempre, pois este presenter não
                suporta análise completa.
        """
        raise NotImplementedError(
            "QualityPresenter does not support present_analysis. "
            "Use AnalysisPresenter for complete reports."
        )

    def present_quality(self, quality: Any) -> Any:
        """Implementa o contrato ``OutputPresenter.present_quality``.

        Args:
            quality: Pontuação de qualidade a ser apresentada.

        Returns:
            ``QualityReport`` formatado.
        """
        return self.present(quality)
