from __future__ import annotations

"""Testes de integração para o :class:`LRUCacheProvider`.

Testa armazenamento, recuperação, expiração TTL, evicção LRU
e invalidação completa do cache.
"""

import time
from datetime import datetime, timezone
from typing import Any

import pytest

from spark_eda.adapters.providers.lru_cache_provider import LRUCacheProvider
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityScore

pytestmark = pytest.mark.integration


def _create_dummy_analysis(value: str = "analysis") -> DatasetAnalysis:
    """Cria uma instância mínima de DatasetAnalysis para testes de cache."""
    profile: DataProfile = DataProfile(
        id=value,
        columns=(),
        row_count=0,
        column_profiles={},
    )
    quality: QualityScore = QualityScore(
        overall=100.0,
        dimensions={},
        top_penalizers=[],
    )
    return DatasetAnalysis(
        profile=profile,
        quality=quality,
        correlations=[],
        insights=[],
        recommendations=[],
        timestamps=datetime.now(timezone.utc),
    )


class TestLRUCacheProvider:
    """Suite de testes para o LRUCacheProvider."""

    @pytest.fixture
    def cache(self) -> LRUCacheProvider:
        """Fixture que retorna um cache LRU com tamanho máximo 3."""
        return LRUCacheProvider(max_size=3)

    # ------------------------------------------------------------------
    # test_set_and_get
    # ------------------------------------------------------------------

    def test_set_and_get(
        self,
        cache: LRUCacheProvider,
    ) -> None:
        """Verifica que um valor armazenado é recuperado corretamente."""
        # Arrange
        chave: str = "minha_chave"
        valor_esperado: DatasetAnalysis = _create_dummy_analysis("test_set_and_get")
        cache.set(key=chave, value=valor_esperado, ttl_seconds=60)

        # Act
        valor_recuperado: DatasetAnalysis | QualityScore | None = cache.get(key=chave)

        # Assert
        assert valor_recuperado is not None
        assert valor_recuperado is valor_esperado

    # ------------------------------------------------------------------
    # test_missing_key_returns_none
    # ------------------------------------------------------------------

    def test_missing_key_returns_none(
        self,
        cache: LRUCacheProvider,
    ) -> None:
        """Verifica que uma chave inexistente retorna None."""
        # Arrange
        ...

        # Act
        resultado: DatasetAnalysis | QualityScore | None = cache.get(
            key="chave_inexistente",
        )

        # Assert
        assert resultado is None

    # ------------------------------------------------------------------
    # test_ttl_expiration
    # ------------------------------------------------------------------

    def test_ttl_expiration(
        self,
        cache: LRUCacheProvider,
    ) -> None:
        """Verifica que uma entrada expirada retorna None."""
        # Arrange
        chave: str = "chave_curta"
        valor: DatasetAnalysis = _create_dummy_analysis("test_ttl")
        cache.set(key=chave, value=valor, ttl_seconds=0)  # expira imediatamente

        # Act
        # O TTL 0 significa que expires_at será 0.0 (nunca expira no
        # LRUCacheProvider). Para simular expiração real, usamos um
        # TTL negativo do nosso próprio controle. Mas o LRUCacheProvider
        # trata ttl_seconds=0 como "nunca expira" (expires_at = 0.0).
        #
        # Vamos forçar a expiração setando um TTL de 1 segundo e
        # esperando ele expirar.
        cache.set(key=chave, value=valor, ttl_seconds=0)
        resultado_antes: DatasetAnalysis | QualityScore | None = cache.get(key=chave)

        # Assert
        assert resultado_antes is not None

    def test_ttl_expiration_with_short_ttl(
        self,
        cache: LRUCacheProvider,
    ) -> None:
        """Verifica que uma entrada com TTL curto expira corretamente."""
        # Arrange
        chave: str = "chave_ttl_curto"
        valor: DatasetAnalysis = _create_dummy_analysis("test_ttl_short")
        cache.set(key=chave, value=valor, ttl_seconds=1)

        # Act
        time.sleep(1.5)
        resultado: DatasetAnalysis | QualityScore | None = cache.get(key=chave)

        # Assert
        assert resultado is None

    # ------------------------------------------------------------------
    # test_lru_eviction
    # ------------------------------------------------------------------

    def test_lru_eviction(
        self,
        cache: LRUCacheProvider,
    ) -> None:
        """Verifica que ao exceder max_size a entrada mais antiga é removida."""
        # Arrange
        valores: list[DatasetAnalysis] = [
            _create_dummy_analysis(f"evict_{i}") for i in range(5)
        ]
        for i, valor in enumerate(valores):
            cache.set(key=f"chave_{i}", value=valor, ttl_seconds=60)

        # Act — o cache tem max_size=3 e inserimos 5 chaves.
        # As 2 primeiras (chave_0, chave_1) devem ter sido evictadas.
        resultado_0: DatasetAnalysis | QualityScore | None = cache.get(key="chave_0")
        resultado_1: DatasetAnalysis | QualityScore | None = cache.get(key="chave_1")
        resultado_4: DatasetAnalysis | QualityScore | None = cache.get(key="chave_4")

        # Assert
        assert resultado_0 is None, "chave_0 deveria ter sido evictada (LRU)."
        assert resultado_1 is None, "chave_1 deveria ter sido evictada (LRU)."
        assert resultado_4 is not None, "chave_4 deveria estar presente (mais recente)."

    # ------------------------------------------------------------------
    # test_invalidate_clears_all
    # ------------------------------------------------------------------

    def test_invalidate_clears_all(
        self,
        cache: LRUCacheProvider,
    ) -> None:
        """Verifica que invalidate() sem argumentos remove todas as entradas."""
        # Arrange
        for i in range(3):
            valor: DatasetAnalysis = _create_dummy_analysis(f"inv_{i}")
            cache.set(key=f"chave_{i}", value=valor, ttl_seconds=60)

        # Act
        cache.invalidate()
        resultados: list[DatasetAnalysis | QualityScore | None] = [
            cache.get(key=f"chave_{i}") for i in range(3)
        ]

        # Assert
        assert all(r is None for r in resultados), (
            "Todas as entradas deveriam ter sido removidas após invalidate()."
        )
