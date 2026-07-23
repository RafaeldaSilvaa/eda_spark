"""Apresentadores de saída para resultados de análise e qualidade."""

from spark_eda.adapters.presenters.analysis_presenter import AnalysisPresenter
from spark_eda.adapters.presenters.quality_presenter import QualityPresenter

__all__ = [
    "AnalysisPresenter",
    "QualityPresenter",
]
