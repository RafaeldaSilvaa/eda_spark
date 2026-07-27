"""Camada de framework — configuração, Spark session e exceções."""

from spark_eda.framework.config import EDAConfig, QualityConfig
from spark_eda.framework.exceptions import (
    AnalysisError,
    CacheError,
    ConfigError,
    DataProviderError,
    QualityError,
    SparkEDAError,
)
from spark_eda.framework.spark_session import get_or_create_spark_session

__all__ = [
    "AnalysisError",
    "CacheError",
    "ConfigError",
    "DataProviderError",
    "EDAConfig",
    "QualityConfig",
    "QualityError",
    "SparkEDAError",
    "get_or_create_spark_session",
]
