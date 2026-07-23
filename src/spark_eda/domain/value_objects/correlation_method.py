"""Métodos de correlação suportados."""

from __future__ import annotations

from enum import Enum


class CorrelationMethod(Enum):
    """Enumeração dos métodos disponíveis para cálculo de correlação."""

    PEARSON = "pearson"
    SPEARMAN = "spearman"
    CRAMERS_V = "cramers_v"
    CORRELATION_RATIO = "correlation_ratio"
    MUTUAL_INFORMATION = "mutual_information"
