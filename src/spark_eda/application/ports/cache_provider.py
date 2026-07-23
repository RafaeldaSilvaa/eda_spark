"""Interface de porta para provedores de cache."""
from __future__ import annotations

from abc import ABC, abstractmethod

from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.quality_score import QualityScore


class CacheProvider(ABC):
    """Interface para provedores de cache de análise e qualidade.

    Permite armazenar resultados computados para evitar o reprocessamento
    de datasets já analisados.
    """

    @abstractmethod
    def get(self, key: str) -> DatasetAnalysis | QualityScore | None:
        """Recupera um valor do cache.

        Args:
            key: Chave única do cache.

        Returns:
            Valor armazenado (DatasetAnalysis ou QualityScore),
            ou None se a chave não existir ou estiver expirada.
        """

    @abstractmethod
    def set(
        self,
        key: str,
        value: DatasetAnalysis | QualityScore,
        ttl_seconds: int,
    ) -> None:
        """Armazena um valor no cache com TTL.

        Args:
            key: Chave única do cache.
            value: Valor a ser armazenado.
            ttl_seconds: Tempo de vida do cache em segundos.
        """

    @abstractmethod
    def invalidate(self, key: str | None = None) -> None:
        """Invalida uma ou todas as entradas do cache.

        Args:
            key: Chave específica para invalidar, ou None para limpar todo o cache.
        """
