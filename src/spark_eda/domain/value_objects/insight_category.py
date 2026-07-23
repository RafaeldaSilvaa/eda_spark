"""Categorias de insights gerados durante a análise."""

from __future__ import annotations

from enum import Enum


class InsightCategory(Enum):
    """Enumeração das categorias de insight que podem ser geradas."""

    SKEWNESS = "skewness"
    NULLS = "nulls"
    CARDINALITY = "cardinality"
    DUPLICATES = "duplicates"
    CONSTANT = "constant"
    NEAR_CONSTANT = "near_constant"
    HIGH_CORRELATION = "high_correlation"
    OUTLIERS = "outliers"
    ZERO_VALUES = "zero_values"
    BUSINESS_PATTERN = "business_pattern"
