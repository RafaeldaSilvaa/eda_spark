"""DTO principal do relatório completo de análise exploratória."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.application.dto.correlation_section import CorrelationSection
from spark_eda.application.dto.distribution_section import DistributionSection
from spark_eda.application.dto.insights_section import InsightsSection
from spark_eda.application.dto.outlier_section import OutlierSection
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.quality_section import QualityReport
from spark_eda.application.dto.recommendations_section import RecommendationsSection
from spark_eda.application.dto.schema_section import SchemaSection
from spark_eda.application.dto.stats_section import StatsSection


@dataclass(frozen=True)
class EDAReport:
    """Relatório completo de análise exploratória de dados.

    Agrega todas as seções do relatório em um único DTO.

    Attributes:
        overview: Seção de visão geral do dataset.
        schema: Seção de esquema e metadados das colunas.
        quality: Relatório de qualidade dos dados.
        stats: Estatísticas descritivas por tipo de coluna.
        distributions: Seção de distribuições de valores.
        correlations: Seção de matriz de correlação.
        outliers: Seção de detecção de outliers.
        insights: Seção de insights gerados.
        recommendations: Seção de recomendações de ação.
    """

    overview: OverviewSection
    schema: SchemaSection
    quality: QualityReport
    stats: StatsSection
    distributions: DistributionSection
    correlations: CorrelationSection
    outliers: OutlierSection
    insights: InsightsSection
    recommendations: RecommendationsSection
