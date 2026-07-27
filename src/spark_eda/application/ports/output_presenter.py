"""Interface de porta para apresentação de saída."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.quality_score import QualityScore


class OutputPresenter(ABC):
    """Interface para apresentação de resultados de análise.

    Suporta diferentes formatos de saída (console, JSON, relatório HTML)
    sem expor implementações concretas à camada de aplicação.
    """

    @abstractmethod
    def present_analysis(self, analysis: DatasetAnalysis) -> Any:
        """Apresenta o resultado completo da análise exploratória.

        Args:
            analysis: DatasetAnalysis contendo profile, qualidade,
                      insights e recomendações.

        Returns:
            Representação formatada da análise (varia por implementação).
        """

    @abstractmethod
    def present_quality(self, quality: QualityScore) -> Any:
        """Apresenta a pontuação de qualidade dos dados.

        Args:
            quality: QualityScore contendo pontuação geral,
                     dimensões e fatores penalizadores.

        Returns:
            Representação formatada da qualidade (varia por implementação).
        """
