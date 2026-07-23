"""Hierarquia de exceções do Spark EDA."""

from __future__ import annotations


class SparkEDAError(Exception):
    """Exceção base para todos os erros do spark_eda."""


class AnalysisError(SparkEDAError):
    """Erro durante a execução da análise exploratória de dados."""


class QualityError(SparkEDAError):
    """Erro durante a avaliação de qualidade dos dados."""


class DataProviderError(SparkEDAError):
    """Erro ao acessar ou fornecer dados de uma fonte externa."""


class CacheError(SparkEDAError):
    """Erro no sistema de cache (leitura, escrita ou expiração)."""


class ConfigError(SparkEDAError):
    """Erro de configuração (valores inválidos ou ausentes)."""
