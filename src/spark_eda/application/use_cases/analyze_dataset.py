"""Caso de uso para análise exploratória de dados completa."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.insight_engine import InsightEngine
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.domain.services.recommendation_engine import RecommendationEngine

logger: logging.Logger = logging.getLogger(__name__)

_DEFAULT_TTL_SECONDS: int = 3600


@dataclass(frozen=True)
class AnalyzeRequest:
    """Solicitação para uma análise exploratória de dados completa.

    Attributes:
        columns: Colunas a analisar, ou None para todas.
        config: Configuração opcional para personalizar a análise.
    """

    columns: list[str] | None
    config: Any


class AnalyzeDatasetUseCase:
    """Caso de uso para análise exploratória de dados completa.

    Orquestra profiling, avaliação de qualidade, geração de insights
    e recomendações, utilizando cache para evitar reprocessamento.

    Attributes:
        _data_provider: Provedor de dados para profiling e fingerprinting.
        _cache_provider: Provedor de cache para armazenar resultados.
        _quality_calculator: Serviço de domínio para cálculo de qualidade.
        _insight_engine: Serviço de domínio para geração de insights.
        _recommendation_engine: Serviço de domínio para geração de recomendações.
    """

    def __init__(
        self,
        data_provider: DataProvider,
        cache_provider: CacheProvider,
        quality_calculator: QualityCalculator,
        insight_engine: InsightEngine,
        recommendation_engine: RecommendationEngine,
    ) -> None:
        self._data_provider: DataProvider = data_provider
        self._cache_provider: CacheProvider = cache_provider
        self._quality_calculator: QualityCalculator = quality_calculator
        self._insight_engine: InsightEngine = insight_engine
        self._recommendation_engine: RecommendationEngine = recommendation_engine

    def _build_cache_key(
        self,
        request: AnalyzeRequest,
        fingerprint: str,
    ) -> str:
        """Constrói uma chave de cache a partir do fingerprint e da solicitação.

        Args:
            request: Solicitação de análise com colunas e configuração.
            fingerprint: Fingerprint do DataFrame.

        Returns:
            Chave de cache única no formato analysis:<fingerprint>:<columns>.
        """
        columns: str = "_".join(sorted(request.columns)) if request.columns else "all"
        return f"analysis:{fingerprint}:{columns}"

    def _try_retrieve_cache(
        self,
        cache_key: str,
    ) -> DatasetAnalysis | None:
        """Tenta recuperar um DatasetAnalysis do cache com tolerância a falhas.

        Args:
            cache_key: Chave do cache.

        Returns:
            DatasetAnalysis se encontrado, None caso contrário.
        """
        try:
            result: Any = self._cache_provider.get(cache_key)
            if isinstance(result, DatasetAnalysis):
                return result
        except Exception as exc:
            logger.warning("Failed to access cache for key '%s': %s", cache_key, exc)
        return None

    def _try_store_cache(
        self,
        cache_key: str,
        analysis: DatasetAnalysis,
        config: Any,
    ) -> None:
        """Tenta armazenar um DatasetAnalysis no cache com tolerância a falhas.

        Args:
            cache_key: Chave do cache.
            analysis: Resultado da análise a ser armazenado.
            config: Configuração que pode conter um TTL personalizado.
        """
        try:
            ttl: int = getattr(config, "cache_ttl_seconds", _DEFAULT_TTL_SECONDS)
            self._cache_provider.set(cache_key, analysis, ttl)
        except Exception as exc:
            logger.warning("Failed to store cache for key '%s': %s", cache_key, exc)

    def execute(
        self,
        request: AnalyzeRequest,
        dataframe: Any,
    ) -> DatasetAnalysis:
        """Executa a análise exploratória de dados completa.

        Fluxo: verificar cache -> calcular profile -> calcular qualidade ->
        gerar insights -> gerar recomendações ->
        armazenar no cache -> retornar DatasetAnalysis.

        Args:
            request: Parâmetros da análise (colunas e configuração).
            dataframe: PySpark DataFrame a ser analisado.

        Returns:
            DatasetAnalysis com profile, qualidade, insights e recomendações.

        Raises:
            ValueError: Se o dataframe for inválido.
            RuntimeError: Se alguma etapa do processamento falhar.
        """
        fingerprint: str = self._data_provider.compute_fingerprint(
            dataframe,
            request.config,
        )
        cache_key: str = self._build_cache_key(request, fingerprint)

        cached_result: DatasetAnalysis | None = self._try_retrieve_cache(cache_key)
        if isinstance(cached_result, DatasetAnalysis):
            logger.info("Analysis retrieved from cache for key: %s", cache_key)
            return cached_result

        try:
            profile: DataProfile = self._data_provider.compute_profile(
                dataframe,
                request.columns,
                request.config,
            )
        except ValueError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Failed to compute dataset profile: {exc}",
            ) from exc

        try:
            quality: QualityScore = self._quality_calculator.calculate(profile)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to calculate data quality: {exc}",
            ) from exc

        try:
            insights = self._insight_engine.generate(profile, quality)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to generate insights: {exc}",
            ) from exc

        try:
            recommendations = self._recommendation_engine.generate(insights, quality)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to generate recommendations: {exc}",
            ) from exc

        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=profile,
            quality=quality,
            correlations=[],  # Correlation is computed separately by SparkDataProvider
            insights=insights,
            recommendations=recommendations,
            timestamps=datetime.now(timezone.utc),
        )

        self._try_store_cache(cache_key, analysis, request.config)

        return analysis
