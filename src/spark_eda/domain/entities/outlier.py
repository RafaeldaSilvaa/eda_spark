"""Informações sobre outliers detectados em uma coluna."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.value_objects.outlier_method import OutlierMethod


@dataclass(frozen=True)
class OutlierInfo:
    """Informações sobre outliers detectados em uma coluna.

    Attributes:
        method: Método utilizado para detecção de outliers.
        count: Número de valores identificados como outliers.
        ratio: Proporção de outliers em relação ao total de valores.
        bounds_lower: Limite inferior para definição de outlier, ou None se não aplicável.
        bounds_upper: Limite superior para definição de outlier, ou None se não aplicável.
    """

    method: OutlierMethod
    count: int
    ratio: float
    bounds_lower: float | None
    bounds_upper: float | None
