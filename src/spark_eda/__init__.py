"""spark_eda — Análise Exploratória de Dados Distribuída para PySpark.

Analise qualquer DataFrame PySpark com uma única linha de código,
produzindo automaticamente estatísticas, métricas de qualidade,
correlações, distribuições, recomendações e insights.

Basic usage:
    >>> import spark_eda
    >>> report = spark_eda.analyze(dataframe)
    >>> display(report)  # HTML in Jupyter
    >>> print(report.quality.score)  # 87.3

    >>> quality = spark_eda.assess_quality(dataframe)
    >>> print(quality.top_penalizers)
"""
from __future__ import annotations

from pyspark.sql import DataFrame

from spark_eda._version import __version__
from spark_eda.adapters.controllers.analyze_controller import AnalyzeController
from spark_eda.adapters.controllers.quality_controller import QualityController
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.quality_section import QualityReport
from spark_eda.framework.config import EDAConfig, QualityConfig
from spark_eda.framework.exceptions import (
    AnalysisError,
    CacheError,
    ConfigError,
    DataProviderError,
    QualityError,
    SparkEDAError,
)


def analyze(
    dataframe: DataFrame,
    config: EDAConfig | None = None,
) -> EDAReport:
    """Executa uma análise exploratória completa em um DataFrame PySpark.

    Args:
        dataframe: DataFrame PySpark a ser analisado.
        config: Configurações opcionais da análise. Se ``None``, usa
            ``EDAConfig()`` com valores padrão.

    Returns:
        ``EDAReport`` contendo todas as seções da análise.
    """
    controller: AnalyzeController = AnalyzeController()
    return controller.execute(dataframe, config or EDAConfig())


def assess_quality(
    dataframe: DataFrame,
    config: QualityConfig | None = None,
) -> QualityReport:
    """Avalia a qualidade dos dados de um DataFrame PySpark.

    Args:
        dataframe: DataFrame PySpark a ser avaliado.
        config: Configurações opcionais de qualidade. Se ``None``, usa
            ``QualityConfig()`` com valores padrão.

    Returns:
        ``QualityReport`` com pontuação de 0 a 100 e detalhamento por fator.
    """
    controller: QualityController = QualityController()
    return controller.execute(dataframe, config or QualityConfig())


__all__ = [
    "AnalysisError",
    "CacheError",
    "ConfigError",
    "DataProviderError",
    "EDAConfig",
    "QualityConfig",
    "QualityError",
    "SparkEDAError",
    "__version__",
    "analyze",
    "assess_quality",
]
