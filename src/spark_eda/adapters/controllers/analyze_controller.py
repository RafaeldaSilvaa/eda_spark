"""Controlador para análise exploratória completa de dados.

Orquestra criação de providers, serviços de domínio e o caso de uso,
expondo um único ponto de entrada que recebe um DataFrame PySpark
e retorna um :class:`EDAReport`.
"""

from __future__ import annotations

import logging
from typing import Any

from pyspark.sql import DataFrame

from spark_eda.adapters.providers.lru_cache_provider import LRUCacheProvider
from spark_eda.adapters.providers.spark_data_provider import SparkDataProvider
from spark_eda.adapters.presenters.analysis_presenter import AnalysisPresenter
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.use_cases.analyze_dataset import AnalyzeDatasetUseCase, AnalyzeRequest
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.services.insight_engine import InsightEngine
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.domain.services.recommendation_engine import RecommendationEngine
from spark_eda.framework.config import EDAConfig

logger: logging.Logger = logging.getLogger(__name__)


class AnalyzeController:
    """Controlador para análise exploratória completa de dados.

    Cria e conecta todas as dependências da camada de adaptadores (providers,
    presenters) e serviços de domínio, delegando a execução para
    o :class:`AnalyzeDatasetUseCase`.

    Attributes:
        _data_provider: Spark provider para profiling.
        _cache_provider: Cache LRU para resultados.
        _presenter: Presenter para conversão de resultados.
        _use_case: Caso de uso de análise completa.
    """

    def __init__(
        self,
        cache_max_size: int = 10,
    ) -> None:
        """Inicializa o controlador com todas as dependências.

        Args:
            cache_max_size: Número máximo de entradas no cache LRU.
        """
        self._data_provider: SparkDataProvider = SparkDataProvider()
        self._cache_provider: LRUCacheProvider = LRUCacheProvider(
            max_size=cache_max_size,
        )
        self._presenter: AnalysisPresenter = AnalysisPresenter()

        quality_calculator: QualityCalculator = QualityCalculator()
        insight_engine: InsightEngine = InsightEngine()
        recommendation_engine: RecommendationEngine = RecommendationEngine()

        self._use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=self._data_provider,
            cache_provider=self._cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

    def execute(
        self,
        dataframe: DataFrame,
        config: EDAConfig | None = None,
    ) -> EDAReport:
        """Executa a análise exploratória completa de dados.

        Cria a requisição com colunas e configuração,
        delega para o caso de uso e converte o resultado em um relatório.

        Args:
            dataframe: DataFrame PySpark a ser analisado.
            config: Configuração da análise. Se None, usa
                valores padrão de :class:`EDAConfig`.

        Returns:
            :class:`EDAReport` com perfil, qualidade, insights
            e recomendações.

        Raises:
            ValueError: Se o DataFrame for inválido.
            RuntimeError: Se o processamento falhar.
        """
        if dataframe is None:
            raise ValueError("DataFrame cannot be None.")

        effective_config: EDAConfig = config or EDAConfig()

        request: AnalyzeRequest = AnalyzeRequest(
            columns=None,
            config=effective_config,
        )

        analysis: DatasetAnalysis = self._use_case.execute(
            request=request,
            dataframe=dataframe,
        )

        report: EDAReport = self._presenter.present_analysis(analysis)

        logger.info(
            "Analysis completed for dataset with %d insights and %d recommendations.",
            len(report.insights.insights),
            len(report.recommendations.recommendations),
        )

        return report
