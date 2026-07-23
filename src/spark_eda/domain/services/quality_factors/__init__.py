"""Módulo para registro e descoberta de fatores de qualidade.

Define o registro central de fatores (:data:`FACTOR_REGISTRY`) e o
decorador :func:`registrar` usado pelos módulos de fator para
autocadastrar suas funções de cálculo.

O registro mapeia nomes de dimensões para funções que, dada uma
instância de :class:`DataProfile <spark_eda.domain.entities.data_profile.DataProfile>`,
retornam a lista de :class:`QualityFactor <spark_eda.domain.entities.quality_score.QualityFactor>`
para aquela dimensão.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityFactor

FACTOR_REGISTRY: dict[str, Callable[[DataProfile], list[QualityFactor]]] = {}
"""Mapeamento de nomes de dimensões para funções de cálculo de fatores.

Cada entrada associa um nome de dimensão (ex.: ``"completude"``,
``"unicidade"``) à função que, dado um :class:`DataProfile`,
produz a lista de :class:`QualityFactor` pertencentes àquela dimensão.
"""


def registrar(
    dimension_name: str,
) -> Callable[[Callable[..., list[QualityFactor]]], Callable[..., list[QualityFactor]]]:
    """Decorador que registra uma função de cálculo no :data:`FACTOR_REGISTRY`.

    A função decorada deve aceitar um :class:`DataProfile` como
    primeiro argumento e retornar ``list[QualityFactor]``.

    Args:
        dimension_name: Nome da dimensão de qualidade à qual esta função
            pertence (ex.: ``"completude"``, ``"unicidade"``).

    Returns:
        O próprio decorador que insere a função no registro.
    """
    def _decorator(
        func: Callable[..., list[QualityFactor]],
    ) -> Callable[..., list[QualityFactor]]:
        FACTOR_REGISTRY[dimension_name] = func  # type: ignore[assignment]
        return func

    return _decorator


# ---------------------------------------------------------------------------
# Imports required so that each module's @registrar decorators are
# executed when the package is loaded.
# ---------------------------------------------------------------------------
from spark_eda.domain.services.quality_factors import (  # noqa: E402  isort:skip
    accuracy,
    completeness,
    consistency,
    timeliness,
    uniqueness,
)
