"""Controladores que orquestram casos de uso com adaptadores."""

from spark_eda.adapters.controllers.analyze_controller import AnalyzeController
from spark_eda.adapters.controllers.quality_controller import QualityController

__all__ = [
    "AnalyzeController",
    "QualityController",
]
