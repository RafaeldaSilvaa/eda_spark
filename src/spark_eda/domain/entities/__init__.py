"""Entidades de domínio do spark_eda."""

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.correlation import Correlation
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.distribution import Distribution, NumericDistribution, CategoricalDistribution, TemporalDistribution
from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.domain.entities.quality_score import QualityScore, QualityDimension, QualityFactor
from spark_eda.domain.entities.recommendation import Recommendation
from spark_eda.domain.entities.statistic import Statistic, NumericStats, CategoricalStats, TemporalStats, TextStats, BooleanStats

__all__ = [
    "ColumnMetadata",
    "ColumnProfile",
    "Correlation",
    "DataProfile",
    "DatasetAnalysis",
    "Distribution",
    "NumericDistribution",
    "CategoricalDistribution",
    "TemporalDistribution",
    "Insight",
    "OutlierInfo",
    "QualityScore",
    "QualityDimension",
    "QualityFactor",
    "Recommendation",
    "Statistic",
    "NumericStats",
    "CategoricalStats",
    "TemporalStats",
    "TextStats",
    "BooleanStats",
]
