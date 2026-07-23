"""Classes de configuração do Spark EDA para análise exploratória e qualidade."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EDAConfig:
    """Configuração para análise exploratória de dados.

    Attributes:
        max_categories: Número máximo de categorias exibidas nas distribuições.
        correlation_methods: Lista de métodos de correlação a computar.
        outlier_method: Método padrão para detecção de outliers.
        enable_insights: Habilita a geração automática de insights.
        enable_recommendations: Habilita a geração de recomendações.
        sampling_threshold: Limite de linhas acima do qual o dataset
            é amostrado para análise.
        cache_ttl_seconds: Tempo de vida do cache em segundos.
    """

    max_categories: int = 30
    correlation_methods: tuple[str, ...] = ("pearson", "spearman", "cramers_v")
    outlier_method: str = "iqr"
    enable_insights: bool = True
    enable_recommendations: bool = True
    sampling_threshold: int = 1_000_000
    cache_ttl_seconds: int = 3600


@dataclass(frozen=True)
class QualityConfig:
    """Configuração para avaliação de qualidade dos dados.

    Attributes:
        weights: Pesos para cada dimensão na pontuação geral de qualidade.
            Dimensões esperadas: ``completeness``, ``uniqueness``,
            ``consistency``, ``freshness``, ``accuracy``.
        near_constant_threshold: Proporção máxima de valores distintos
            para uma coluna ser considerada quase constante.
    """

    weights: dict[str, float] = field(
        default_factory=lambda: {
            "completeness": 0.25,
            "uniqueness": 0.20,
            "consistency": 0.20,
            "timeliness": 0.15,
            "accuracy": 0.20,
        }
    )
    near_constant_threshold: float = 0.01
