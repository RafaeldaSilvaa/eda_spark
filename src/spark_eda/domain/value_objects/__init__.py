"""Objetos de valor (enums) do domínio spark_eda."""

from spark_eda.domain.value_objects.correlation_method import CorrelationMethod
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.inferred_type import InferredType
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.outlier_method import OutlierMethod
from spark_eda.domain.value_objects.recommendation_category import RecommendationCategory
from spark_eda.domain.value_objects.severity import Severity

__all__ = [
    "CorrelationMethod",
    "DataType",
    "InferredType",
    "InsightCategory",
    "OutlierMethod",
    "RecommendationCategory",
    "Severity",
]
