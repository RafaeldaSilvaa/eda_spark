"""Controlador para avaliação de qualidade de dados.

Orquestra criação de providers, serviços de domínio e o caso de uso,
expondo um único ponto de entrada que recebe um DataFrame PySpark
e retorna um :class:`QualityReport`.
"""

from __future__ import annotations

import logging
from typing import Any

from pyspark.sql import DataFrame

from spark_eda.adapters.providers.lru_cache_provider import LRUCacheProvider
from spark_eda.adapters.providers.spark_data_provider import SparkDataProvider
from spark_eda.adapters.presenters.quality_presenter import QualityPresenter
from spark_eda.application.dto.quality_section import QualityReport
from spark_eda.application.use_cases.assess_quality import AssessQualityUseCase, QualityRequest
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.framework.config import QualityConfig

logger: logging.Logger = logging.getLogger(__name__)


class QualityController:
    """Controlador para avaliação de qualidade de dados.

    Cria e conecta todas as dependências da camada de adaptadores (providers,
    presenters) e serviços de domínio, delegando a execução para
    o :class:`AssessQualityUseCase`.

    Attributes:
        _data_provider: Spark provider para profiling.
        _cache_provider: Cache LRU para resultados.
        _presenter: Presenter para conversão de resultados.
        _use_case: Caso de uso de avaliação de qualidade.
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
        self._presenter: QualityPresenter = QualityPresenter()

        quality_calculator: QualityCalculator = QualityCalculator()

        self._use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=self._data_provider,
            cache_provider=self._cache_provider,
            quality_calculator=quality_calculator,
        )

    def execute(
        self,
        dataframe: DataFrame,
        config: QualityConfig | None = None,
    ) -> QualityReport:
        """Executa a avaliação de qualidade dos dados.

        Cria a requisição com colunas e configuração,
        delega para o caso de uso e converte o resultado em um relatório.

        Args:
            dataframe: DataFrame PySpark a ser avaliado.
            config: Configuração da avaliação. Se None, usa
                valores padrão de :class:`QualityConfig`.

        Returns:
            :class:`QualityReport` com a pontuação de qualidade.

        Raises:
            ValueError: Se o DataFrame for inválido.
            RuntimeError: Se o processamento falhar.
        """
        if dataframe is None:
            raise ValueError("DataFrame cannot be None.")

        effective_config: QualityConfig = config or QualityConfig()

        request: QualityRequest = QualityRequest(
            columns=None,
            config=effective_config,
        )

        quality: QualityScore = self._use_case.execute(
            request=request,
            dataframe=dataframe,
        )

        report: QualityReport = self._presenter.present_quality(quality)

        logger.info(
            "Quality assessment completed: overall score %.2f "
            "with %d dimensions evaluated.",
            quality.overall,
            len(quality.dimensions),
        )

        return report
