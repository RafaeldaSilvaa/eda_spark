"""Objetos de transferência de dados da camada de aplicação."""

from spark_eda.application.dto.eda_report import EDAReport, QualityReport
from spark_eda.application.dto.stats_section import StatsSection, NumericStatsDTO, CategoricalStatsDTO, TemporalStatsDTO, TextStatsDTO, BooleanStatsDTO
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.schema_section import SchemaSection, SchemaColumn
from spark_eda.application.dto.correlation_section import CorrelationSection, CorrelationEntry
from spark_eda.application.dto.distribution_section import DistributionSection, HistogramBin, FrequencyEntry, TemporalPoint
from spark_eda.application.dto.outlier_section import OutlierSection, OutlierSummary
from spark_eda.application.dto.insights_section import InsightsSection, InsightDTO
from spark_eda.application.dto.recommendations_section import RecommendationsSection, RecommendationDTO
from spark_eda.application.dto.quality_section import QualityReport as QR, QualityFactorReport, QualityDimensionReport

__all__ = [
    "EDAReport",
    "QualityReport",
    "StatsSection",
    "NumericStatsDTO",
    "CategoricalStatsDTO",
    "TemporalStatsDTO",
    "TextStatsDTO",
    "BooleanStatsDTO",
    "OverviewSection",
    "SchemaSection",
    "SchemaColumn",
    "CorrelationSection",
    "CorrelationEntry",
    "DistributionSection",
    "HistogramBin",
    "FrequencyEntry",
    "TemporalPoint",
    "OutlierSection",
    "OutlierSummary",
    "InsightsSection",
    "InsightDTO",
    "RecommendationsSection",
    "RecommendationDTO",
    "QualityFactorReport",
    "QualityDimensionReport",
]
