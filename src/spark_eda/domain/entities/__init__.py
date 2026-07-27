"""Entidades de domínio do spark_eda."""

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.correlation import Correlation
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.distribution import (
    CategoricalDistribution,
    Distribution,
    NumericDistribution,
    TemporalDistribution,
)
from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.domain.entities.quality_score import QualityDimension, QualityFactor, QualityScore
from spark_eda.domain.entities.recommendation import Recommendation
from spark_eda.domain.entities.statistic import (
    BooleanStats,
    CategoricalStats,
    NumericStats,
    Statistic,
    TemporalStats,
    TextStats,
)

__all__ = [
    "BooleanStats",
    "CategoricalDistribution",
    "CategoricalStats",
    "ColumnMetadata",
    "ColumnProfile",
    "Correlation",
    "DataProfile",
    "DatasetAnalysis",
    "Distribution",
    "Insight",
    "NumericDistribution",
    "NumericStats",
    "OutlierInfo",
    "QualityDimension",
    "QualityFactor",
    "QualityScore",
    "Recommendation",
    "Statistic",
    "TemporalDistribution",
    "TemporalStats",
    "TextStats",
]
