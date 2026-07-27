"""Caso de uso para avaliação de qualidade dos dados."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from spark_eda.application.exceptions import DataProviderError, QualityError
from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.quality_calculator import QualityCalculator

logger: logging.Logger = logging.getLogger(__name__)

_DEFAULT_TTL_SECONDS: int = 3600


@dataclass(frozen=True)
class QualityRequest:
    """Solicitação para avaliação de qualidade dos dados.

    Attributes:
        columns: Colunas a avaliar, ou None para todas.
        config: Configuração opcional para personalizar a avaliação.
    """

    columns: list[str] | None
    config: Any


class AssessQualityUseCase:
    """Caso de uso para avaliação de qualidade dos dados.

    Orquestra as etapas de profiling e cálculo de qualidade,
    utilizando cache para evitar reprocessamento de datasets já avaliados.

    Attributes:
        _data_provider: Provedor de dados para profiling e fingerprinting.
        _cache_provider: Provedor de cache para armazenar resultados.
        _quality_calculator: Serviço de domínio para cálculo de qualidade.
    """

    def __init__(
        self,
        data_provider: DataProvider,
        cache_provider: CacheProvider,
        quality_calculator: QualityCalculator,
    ) -> None:
        self._data_provider: DataProvider = data_provider
        self._cache_provider: CacheProvider = cache_provider
        self._quality_calculator: QualityCalculator = quality_calculator

    def _build_cache_key(
        self,
        request: QualityRequest,
        fingerprint: str,
    ) -> str:
        """Constrói uma chave de cache a partir do fingerprint e da solicitação.

        Args:
            request: Solicitação de qualidade com colunas e configuração.
            fingerprint: Fingerprint do DataFrame.

        Returns:
            Chave de cache única no formato quality:<fingerprint>:<columns>.
        """
        columns: str = "_".join(sorted(request.columns)) if request.columns else "all"
        return f"quality:{fingerprint}:{columns}"

    def _try_retrieve_cache(
        self,
        cache_key: str,
    ) -> QualityScore | None:
        """Tenta recuperar um QualityScore do cache com tolerância a falhas.

        Args:
            cache_key: Chave do cache.

        Returns:
            QualityScore se encontrado, None caso contrário.
        """
        try:
            result: Any = self._cache_provider.get(cache_key)
            if isinstance(result, QualityScore):
                return result
        except Exception as exc:
            logger.warning("Failed to access cache for key '%s': %s", cache_key, exc)
        return None

    def _try_store_cache(
        self,
        cache_key: str,
        quality: QualityScore,
        config: Any,
    ) -> None:
        """Tenta armazenar um QualityScore no cache com tolerância a falhas.

        Args:
            cache_key: Chave do cache.
            quality: Resultado de qualidade a ser armazenado.
            config: Configuração que pode conter um TTL personalizado.
        """
        try:
            ttl: int = getattr(config, "cache_ttl_seconds", _DEFAULT_TTL_SECONDS)
            self._cache_provider.set(cache_key, quality, ttl)
        except Exception as exc:
            logger.warning("Failed to store cache for key '%s': %s", cache_key, exc)

    def _get_profile(
        self,
        dataframe: Any,
        request: QualityRequest,
    ) -> DataProfile:
        """Obtém o perfil do dataset via DataProvider com tratamento de erro.

        Args:
            dataframe: PySpark DataFrame.
            request: Solicitação com colunas e configuração.

        Returns:
            DataProfile calculado a partir do DataFrame.

        Raises:
            ValueError: Se as colunas solicitadas não existirem.
            DataProviderError: Se o profiling falhar por outro motivo.
        """
        try:
            return self._data_provider.compute_profile(
                dataframe,
                request.columns,
                request.config,
            )
        except Exception as exc:
            raise DataProviderError(
                f"Failed to compute dataset profile: {exc}",
            ) from exc

    def execute(
        self,
        request: QualityRequest,
        dataframe: Any,
    ) -> QualityScore:
        """Executa a avaliação de qualidade dos dados.

        Fluxo: verificar cache -> calcular profile ->
        calcular qualidade -> armazenar no cache -> retornar QualityScore.

        Args:
            request: Parâmetros da avaliação (colunas e configuração).
            dataframe: PySpark DataFrame a ser avaliado.

        Returns:
            QualityScore com pontuação geral, dimensões e fatores.

        Raises:
            ValueError: Se o dataframe for inválido.
            DataProviderError: Se o profiling falhar.
            QualityError: Se o cálculo de qualidade falhar.
        """
        fingerprint: str = self._data_provider.compute_fingerprint(
            dataframe,
            request.config,
        )
        cache_key: str = self._build_cache_key(request, fingerprint)

        cached_result: QualityScore | None = self._try_retrieve_cache(cache_key)
        if isinstance(cached_result, QualityScore):
            logger.info("Quality retrieved from cache for key: %s", cache_key)
            return cached_result

        profile: DataProfile = self._get_profile(dataframe, request)

        try:
            quality: QualityScore = self._quality_calculator.calculate(profile)
        except Exception as exc:
            raise QualityError(
                f"Failed to calculate data quality: {exc}",
            ) from exc

        self._try_store_cache(cache_key, quality, request.config)

        return quality
