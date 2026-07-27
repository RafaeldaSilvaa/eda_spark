"""Hierarquia de exceções do Spark EDA (re-export da camada de aplicação)."""

from __future__ import annotations

from spark_eda.application.exceptions import (
    AnalysisError,
    CacheError,
    ConfigError,
    DataProviderError,
    QualityError,
    SparkEDAError,
)

__all__ = [
    "AnalysisError",
    "CacheError",
    "ConfigError",
    "DataProviderError",
    "QualityError",
    "SparkEDAError",
]
