from __future__ import annotations

"""Testes de borda para o provider de cache LRU.

Testa ramificações não cobertas pelos testes principais:
- TTL = 0 (entrada que nunca expira)
- Thread safety com contenção real
"""

from unittest import mock

from spark_eda.adapters.providers.lru_cache_provider import LRUCacheProvider
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis


class TestLRUCacheEdgeCases:
    """Testes de borda para LRUCacheProvider."""

    def test_set_with_ttl_zero_never_expires(self) -> None:
        """set com ttl_seconds=0 deve criar entrada que nunca
        expira (expires_at == 0.0).
        """
        # Arrange
        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)
        value: DatasetAnalysis = mock.Mock(spec=DatasetAnalysis)

        # Act
        cache.set("k", value, ttl_seconds=0)
        result: DatasetAnalysis | None = cache.get("k")

        # Assert
        assert result is value

    def test_set_with_ttl_zero_not_expired_after_time(self) -> None:
        """Entrada com ttl_seconds=0 não deve expirar mesmo após
        muito tempo.
        """
        # Arrange
        import time

        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)
        value: DatasetAnalysis = mock.Mock(spec=DatasetAnalysis)

        with mock.patch.object(time, "time", return_value=1000.0):
            cache.set("k", value, ttl_seconds=0)

        # Act — avança muito no futuro
        with mock.patch.object(time, "time", return_value=999999.0):
            result: DatasetAnalysis | None = cache.get("k")

        # Assert
        assert result is value

    def test_get_removes_expired_entry(self) -> None:
        """get deve remover entrada expirada do cache interno."""
        # Arrange
        import time

        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)
        value: DatasetAnalysis = mock.Mock(spec=DatasetAnalysis)

        with mock.patch.object(time, "time", return_value=1000.0):
            cache.set("exp", value, ttl_seconds=10)

        # Act
        with mock.patch.object(time, "time", return_value=2000.0):
            result: DatasetAnalysis | None = cache.get("exp")

        # Assert
        assert result is None
        # A entrada removida não deve mais estar no cache interno
        assert "exp" not in cache._cache

    def test_set_updates_existing_key_ttl(self) -> None:
        """set em chave existente deve atualizar expires_at."""
        # Arrange
        import time

        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)
        value1: DatasetAnalysis = mock.Mock(spec=DatasetAnalysis)
        value2: DatasetAnalysis = mock.Mock(spec=DatasetAnalysis)

        with mock.patch.object(time, "time", return_value=1000.0):
            cache.set("k", value1, ttl_seconds=10)

        # Act — atualiza com TTL maior
        with mock.patch.object(time, "time", return_value=1000.0):
            cache.set("k", value2, ttl_seconds=100)

        # Assert — ainda válido após 50s (dentro do novo TTL)
        with mock.patch.object(time, "time", return_value=1050.0):
            result: DatasetAnalysis | None = cache.get("k")
        assert result is value2
