"""Métodos de detecção de outliers."""

from __future__ import annotations

from enum import Enum


class OutlierMethod(Enum):
    """Enumeração dos métodos disponíveis para detecção de outliers."""

    IQR = "iqr"
    ZSCORE = "zscore"
    MAD = "mad"
