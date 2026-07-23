"""Provider de cache LRU com suporte a TTL.

Implementa a interface :class:`CacheProvider` usando um dicionário
ordenado (LRU) com limite de tamanho, expiração por TTL e segurança
de thread.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict

from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.application.ports.cache_provider import CacheProvider

_CacheValue = DatasetAnalysis | QualityScore


class _CacheEntry:
    """Entrada individual de cache com valor e timestamp de expiração.

    Attributes:
        value: Valor armazenado (DatasetAnalysis ou QualityScore).
        expires_at: Timestamp Unix (segundos) indicando quando esta
            entrada expira. Se 0, nunca expira.
    """

    __slots__ = ("value", "expires_at")

    def __init__(
        self,
        value: _CacheValue,
        expires_at: float,
    ) -> None:
        self.value: _CacheValue = value
        self.expires_at: float = expires_at


class LRUCacheProvider(CacheProvider):
    """Cache LRU thread-safe com limite de tamanho e expiração por TTL.

    Quando o cache atinge ``max_size``, a entrada menos recentemente
    acessada (LRU) é removida. Entradas expiradas são removidas de
    forma lazy durante operações de leitura.

    Attributes:
        max_size: Número máximo de entradas no cache.
        _cache: Dicionário ordenado para rastreamento LRU.
        _lock: Lock para operações thread-safe.
    """

    def __init__(self, max_size: int = 10) -> None:
        """Inicializa o cache LRU.

        Args:
            max_size: Número máximo de entradas. Quando excedido,
                a entrada mais antiga é removida. Deve ser >= 1.
        """
        if max_size < 1:
            raise ValueError(f"max_size must be >= 1, got: {max_size}")

        self.max_size: int = max_size
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock: threading.Lock = threading.Lock()

    def get(self, key: str) -> _CacheValue | None:
        """Recupera um valor do cache.

        Move a entrada para o final da ordem LRU (mais recentemente
        usada) se encontrada e não expirada. Remove entradas expiradas
        durante a busca (remoção lazy).

        Args:
            key: Chave única do cache.

        Returns:
            O valor armazenado, ou None se a chave não existir
            ou estiver expirada.
        """
        with self._lock:
            entry: _CacheEntry | None = self._cache.get(key)

            if entry is None:
                return None

            if self._is_expired(entry):
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            return entry.value

    def set(
        self,
        key: str,
        value: _CacheValue,
        ttl_seconds: int,
    ) -> None:
        """Armazena um valor no cache com um TTL.

        Se a chave já existir, o valor é atualizado e movido para
        o final da ordem LRU. Se o cache estiver cheio, a entrada
        menos recentemente acessada é removida.

        Args:
            key: Chave única do cache.
            value: Valor a ser armazenado.
            ttl_seconds: Tempo de vida em segundos. Use 0 para entradas
                que nunca expiram (não recomendado).
        """
        expires_at: float = 0.0
        if ttl_seconds > 0:
            expires_at = time.time() + ttl_seconds

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = _CacheEntry(value=value, expires_at=expires_at)

            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def invalidate(self, key: str | None = None) -> None:
        """Invalida entradas do cache.

        Args:
            key: Chave específica a ser invalidada. Se None, limpa
                todo o cache.
        """
        with self._lock:
            if key is None:
                self._cache.clear()
            else:
                self._cache.pop(key, None)

    def _is_expired(self, entry: _CacheEntry) -> bool:
        """Verifica se uma entrada de cache está expirada.

        Args:
            entry: Entrada de cache a ser verificada.

        Returns:
            True se a entrada estiver expirada, False caso contrário.
        """
        if entry.expires_at == 0.0:
            return False
        return time.time() > entry.expires_at
