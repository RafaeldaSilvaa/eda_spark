"""Objetos de transferência de dados da camada de aplicação."""

from spark_eda.adapters.omniroute.models import AiCommentary
from spark_eda.application.dto.correlation_section import CorrelationEntry, CorrelationSection
from spark_eda.application.dto.distribution_section import (
    DistributionSection,
    FrequencyEntry,
    HistogramBin,
    TemporalPoint,
)
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.insights_section import InsightDTO, InsightsSection
from spark_eda.application.dto.outlier_section import OutlierSection, OutlierSummary
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.quality_section import QualityDimensionReport, QualityFactorReport, QualityReport
from spark_eda.application.dto.recommendations_section import RecommendationDTO, RecommendationsSection
from spark_eda.application.dto.schema_section import SchemaColumn, SchemaSection
from spark_eda.application.dto.stats_section import (
    BooleanStatsDTO,
    CategoricalStatsDTO,
    NumericStatsDTO,
    StatsSection,
    TemporalStatsDTO,
    TextStatsDTO,
)

__all__ = [
    "AiCommentary",
    "BooleanStatsDTO",
    "CategoricalStatsDTO",
    "CorrelationEntry",
    "CorrelationSection",
    "DistributionSection",
    "EDAReport",
    "FrequencyEntry",
    "HistogramBin",
    "InsightDTO",
    "InsightsSection",
    "NumericStatsDTO",
    "OutlierSection",
    "OutlierSummary",
    "OverviewSection",
    "QualityDimensionReport",
    "QualityFactorReport",
    "QualityReport",
    "RecommendationDTO",
    "RecommendationsSection",
    "SchemaColumn",
    "SchemaSection",
    "StatsSection",
    "TemporalPoint",
    "TemporalStatsDTO",
    "TextStatsDTO",
]
