from __future__ import annotations

"""Testes contratuais para os objetos de valor do domínio.

Verifica que todos os enums possuem os membros esperados,
são enums válidos e podem ser usados em comparações.
"""

from enum import Enum

from spark_eda.domain.value_objects.correlation_method import CorrelationMethod
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.inferred_type import InferredType
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.outlier_method import OutlierMethod
from spark_eda.domain.value_objects.recommendation_category import RecommendationCategory
from spark_eda.domain.value_objects.severity import Severity


class TestDataType:
    """Testes para o enum DataType."""

    def test_all_members_present(self) -> None:
        expected: set[str] = {
            "STRING",
            "INTEGER",
            "LONG",
            "DOUBLE",
            "BOOLEAN",
            "DATE",
            "TIMESTAMP",
            "DECIMAL",
            "BINARY",
            "ARRAY",
            "MAP",
            "STRUCT",
            "OTHER",
        }
        actual: set[str] = {m.name for m in DataType}
        assert actual == expected

    def test_is_enum(self) -> None:
        assert issubclass(DataType, Enum)

    def test_member_values(self) -> None:
        assert DataType.STRING.value == "string"
        assert DataType.INTEGER.value == "integer"
        assert DataType.DOUBLE.value == "double"


class TestInferredType:
    """Testes para o enum InferredType."""

    def test_all_members_present(self) -> None:
        expected: set[str] = {
            "CPF",
            "CNPJ",
            "EMAIL",
            "UUID",
            "URL",
            "IPV4",
            "CEP",
            "PHONE_BR",
            "CREDIT_CARD",
            "AUTO_INCREMENT",
            "TECHNICAL_KEY",
            "NONE",
        }
        actual: set[str] = {m.name for m in InferredType}
        assert actual == expected

    def test_is_enum(self) -> None:
        assert issubclass(InferredType, Enum)

    def test_none_value(self) -> None:
        assert InferredType.NONE.value == "none"


class TestInsightCategory:
    """Testes para o enum InsightCategory."""

    def test_all_members_present(self) -> None:
        expected: set[str] = {
            "NULLS",
            "OUTLIERS",
            "SKEWNESS",
            "CARDINALITY",
            "CONSTANT",
            "NEAR_CONSTANT",
            "DUPLICATES",
            "BUSINESS_PATTERN",
            "ZERO_VALUES",
            "HIGH_CORRELATION",
        }
        actual: set[str] = {m.name for m in InsightCategory}
        assert actual == expected

    def test_is_enum(self) -> None:
        assert issubclass(InsightCategory, Enum)

    def test_member_comparison(self) -> None:
        assert InsightCategory.NULLS == InsightCategory.NULLS
        assert InsightCategory.NULLS != InsightCategory.OUTLIERS


class TestOutlierMethod:
    """Testes para o enum OutlierMethod."""

    def test_all_members_present(self) -> None:
        expected: set[str] = {"IQR", "ZSCORE", "MAD"}
        actual: set[str] = {m.name for m in OutlierMethod}
        assert actual == expected

    def test_is_enum(self) -> None:
        assert issubclass(OutlierMethod, Enum)

    def test_member_values(self) -> None:
        assert OutlierMethod.IQR.value == "iqr"
        assert OutlierMethod.ZSCORE.value == "zscore"


class TestRecommendationCategory:
    """Testes para o enum RecommendationCategory."""

    def test_all_members_present(self) -> None:
        expected: set[str] = {
            "NULL_TREATMENT",
            "OUTLIER_TREATMENT",
            "TYPE_FIX",
            "PERFORMANCE",
            "SCHEMA",
            "BUSINESS_RULE",
        }
        actual: set[str] = {m.name for m in RecommendationCategory}
        assert actual == expected

    def test_is_enum(self) -> None:
        assert issubclass(RecommendationCategory, Enum)


class TestSeverity:
    """Testes para o enum Severity."""

    def test_all_members_present(self) -> None:
        expected: set[str] = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        actual: set[str] = {m.name for m in Severity}
        assert actual == expected

    def test_is_enum(self) -> None:
        assert issubclass(Severity, Enum)

    def test_members_defined_in_order(self) -> None:
        order: list[str] = [m.name for m in Severity]
        low_idx: int = order.index("LOW")
        critical_idx: int = order.index("CRITICAL")
        assert low_idx < critical_idx


class TestCorrelationMethod:
    """Testes para o enum CorrelationMethod."""

    def test_all_members_present(self) -> None:
        expected: set[str] = {"PEARSON", "SPEARMAN", "CRAMERS_V", "CORRELATION_RATIO", "MUTUAL_INFORMATION"}
        actual: set[str] = {m.name for m in CorrelationMethod}
        assert actual == expected

    def test_is_enum(self) -> None:
        assert issubclass(CorrelationMethod, Enum)
