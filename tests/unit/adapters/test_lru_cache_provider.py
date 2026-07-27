from __future__ import annotations

"""Testes para o provider de cache LRU.

Testa o LRUCacheProvider com operações de set/get, expiração,
evicção LRU, invalidação e segurança de thread.
"""

from unittest import mock

import pytest

from spark_eda.adapters.providers.lru_cache_provider import LRUCacheProvider
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.quality_score import QualityScore


class TestLRUCacheProvider:
    """Testes para o cache LRU com suporte a TTL."""

    def test_set_and_get(self) -> None:
        """Armazenar um valor com TTL e recuperá-lo imediatamente deve
        retornar o valor correto.
        """
        # Arrange
        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)

        # Act
        cache.set("chave:1", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)
        result: DatasetAnalysis | QualityScore | None = cache.get("chave:1")

        # Assert
        assert result is not None

    def test_get_returns_none_for_missing_key(self) -> None:
        """Recuperar uma chave inexistente deve retornar None."""
        # Arrange
        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)

        # Act
        result: DatasetAnalysis | QualityScore | None = cache.get("nao_existe")

        # Assert
        assert result is None

    def test_get_returns_none_for_expired_entry(self) -> None:
        """Uma entrada expirada deve retornar None ao ser consultada."""
        # Arrange
        import time

        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)

        with mock.patch.object(time, "time", return_value=1000.0):
            cache.set("k", mock.Mock(spec=QualityScore), ttl_seconds=10)

        # Act — avança 11s no futuro
        with mock.patch.object(time, "time", return_value=1011.0):
            result: DatasetAnalysis | QualityScore | None = cache.get("k")

        # Assert
        assert result is None

    def test_lru_eviction(self) -> None:
        """Quando o cache atinge max_size, a entrada menos recentemente
        acessada deve ser removida.
        """
        # Arrange
        cache: LRUCacheProvider = LRUCacheProvider(max_size=2)

        # Act
        cache.set("a", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)
        cache.set("b", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)
        cache.set("c", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)

        # Assert
        assert cache.get("a") is None  # evictado (LRU)
        assert cache.get("b") is not None
        assert cache.get("c") is not None

    def test_invalidate_single_key(self) -> None:
        """Invalidar uma chave específica deve removê-la do cache."""
        # Arrange
        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)
        cache.set("x", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)
        cache.set("y", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)

        # Act
        cache.invalidate("x")

        # Assert
        assert cache.get("x") is None
        assert cache.get("y") is not None

    def test_invalidate_all(self) -> None:
        """Invalidar sem chave (None) deve limpar todo o cache."""
        # Arrange
        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)
        cache.set("a", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)
        cache.set("b", mock.Mock(spec=DatasetAnalysis), ttl_seconds=3600)

        # Act
        cache.invalidate(None)

        # Assert
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_update_existing_key(self) -> None:
        """Atualizar uma chave existente deve sobrescrever o valor."""
        # Arrange
        cache: LRUCacheProvider = LRUCacheProvider(max_size=10)
        value_old: DatasetAnalysis = mock.Mock(spec=DatasetAnalysis)
        value_new: QualityScore = mock.Mock(spec=QualityScore)
        cache.set("k", value_old, ttl_seconds=3600)

        # Act
        cache.set("k", value_new, ttl_seconds=3600)
        result: DatasetAnalysis | QualityScore | None = cache.get("k")

        # Assert
        assert result is value_new

    def test_thread_safety(self) -> None:
        """Operações concorrentes de set/get não devem causar crash."""
        # Arrange
        import threading

        cache: LRUCacheProvider = LRUCacheProvider(max_size=5)
        errors: list[Exception] = []

        def worker(idx: int) -> None:
            try:
                for _ in range(50):
                    key: str = f"t{idx}"
                    cache.set(key, mock.Mock(spec=DatasetAnalysis), ttl_seconds=10)
                    cache.get(key)
                    cache.invalidate(key)
            except Exception as e:
                errors.append(e)

        threads: list[threading.Thread] = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

        # Act
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert
        assert not errors

    def test_max_size_must_be_positive(self) -> None:
        """max_size < 1 deve levantar ValueError."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="max_size must be >= 1"):
            LRUCacheProvider(max_size=0)

        with pytest.raises(ValueError, match="max_size must be >= 1"):
            LRUCacheProvider(max_size=-1)
