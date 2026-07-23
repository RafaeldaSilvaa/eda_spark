"""Interfaces de porta da camada de aplicação."""

from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.output_presenter import OutputPresenter

__all__ = [
    "DataProvider",
    "CacheProvider",
    "OutputPresenter",
]
