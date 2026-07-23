from __future__ import annotations

"""Testes para o motor de geração de recomendações.

Testa o serviço RecommendationEngine com insights criados diretamente,
verificando o mapeamento de categorias, prioridades e mensagens.
"""

from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.entities.recommendation import Recommendation
from spark_eda.domain.services.recommendation_engine import RecommendationEngine
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.recommendation_category import RecommendationCategory
from spark_eda.domain.value_objects.severity import Severity


def _any_quality() -> QualityScore:
    """QualityScore neutro para testes."""
    return QualityScore(overall=100.0, dimensions={}, top_penalizers=[])


class TestRecommendationEngine:
    """Testes para o motor de geração de recomendações."""

    def test_empty_insights_returns_empty_recommendations(self) -> None:
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([], _any_quality())
        assert result == []

    def test_null_insight_returns_null_treatment_recommendation(self) -> None:
        insight: Insight = Insight(
            column="idade",
            category=InsightCategory.NULLS,
            severity=Severity.MEDIUM,
            message="40% nulos",
            metric_value=0.4,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert any(r.category == RecommendationCategory.NULL_TREATMENT for r in result)

    def test_null_insight_critical_severity_returns_two_recommendations(self) -> None:
        insight: Insight = Insight(
            column="renda",
            category=InsightCategory.NULLS,
            severity=Severity.CRITICAL,
            message="90% nulos",
            metric_value=0.9,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 2
        assert all(r.priority == 1 for r in result)

    def test_null_insight_low_severity_returns_one_recommendation(self) -> None:
        insight: Insight = Insight(
            column="telefone",
            category=InsightCategory.NULLS,
            severity=Severity.LOW,
            message="5% nulos",
            metric_value=0.05,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].priority == 4

    def test_outlier_insight_returns_outlier_treatment(self) -> None:
        insight: Insight = Insight(
            column="valor",
            category=InsightCategory.OUTLIERS,
            severity=Severity.HIGH,
            message="10% outliers",
            metric_value=0.1,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.OUTLIER_TREATMENT
        assert result[0].priority == 2

    def test_skewness_insight_returns_type_fix(self) -> None:
        insight: Insight = Insight(
            column="skew_col",
            category=InsightCategory.SKEWNESS,
            severity=Severity.MEDIUM,
            message="Skewness = 3.5",
            metric_value=3.5,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.TYPE_FIX

    def test_cardinality_insight_returns_performance(self) -> None:
        insight: Insight = Insight(
            column="id_unico",
            category=InsightCategory.CARDINALITY,
            severity=Severity.LOW,
            message="Alta cardinalidade",
            metric_value=0.99,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.PERFORMANCE

    def test_constant_insight_returns_schema(self) -> None:
        insight: Insight = Insight(
            column="pais",
            category=InsightCategory.CONSTANT,
            severity=Severity.MEDIUM,
            message="Coluna constante",
            metric_value=1.0,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.SCHEMA

    def test_near_constant_insight_returns_schema(self) -> None:
        insight: Insight = Insight(
            column="flag",
            category=InsightCategory.NEAR_CONSTANT,
            severity=Severity.MEDIUM,
            message="Quase constante",
            metric_value=0.95,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.SCHEMA

    def test_duplicate_insight_returns_schema(self) -> None:
        insight: Insight = Insight(
            column=None,
            category=InsightCategory.DUPLICATES,
            severity=Severity.HIGH,
            message="20% duplicatas",
            metric_value=0.2,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.SCHEMA
        assert result[0].column is None

    def test_business_pattern_insight_returns_business_rule(self) -> None:
        insight: Insight = Insight(
            column="cpf",
            category=InsightCategory.BUSINESS_PATTERN,
            severity=Severity.CRITICAL,
            message="CPF inválido detectado",
            metric_value=0.3,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.BUSINESS_RULE

    def test_zero_values_insight_returns_business_rule(self) -> None:
        insight: Insight = Insight(
            column="salario",
            category=InsightCategory.ZERO_VALUES,
            severity=Severity.MEDIUM,
            message="Zeros atípicos",
            metric_value=0.15,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 1
        assert result[0].category == RecommendationCategory.BUSINESS_RULE

    def test_recommendations_sorted_by_priority(self) -> None:
        low_insight: Insight = Insight(
            column="a", category=InsightCategory.NULLS, severity=Severity.LOW,
            message="baixo", metric_value=0.01,
        )
        high_insight: Insight = Insight(
            column="b", category=InsightCategory.OUTLIERS, severity=Severity.CRITICAL,
            message="critico", metric_value=0.5,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([low_insight, high_insight], _any_quality())

        priorities: list[int] = [r.priority for r in result]
        assert priorities == sorted(priorities)

    def test_unknown_category_produces_no_recommendation(self) -> None:
        insight: Insight = Insight(
            column="x",
            category="UNKNOWN_CATEGORY",  # type: ignore[arg-type]
            severity=Severity.MEDIUM,
            message="desconhecido",
            metric_value=None,
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert len(result) == 0

    def test_priority_mapping_all_severities(self) -> None:
        engine: RecommendationEngine = RecommendationEngine()
        pairs: list[tuple[Severity, int]] = [
            (Severity.CRITICAL, 1),
            (Severity.HIGH, 2),
            (Severity.MEDIUM, 3),
            (Severity.LOW, 4),
        ]
        for severity, expected_priority in pairs:
            insight: Insight = Insight(
                column="c", category=InsightCategory.CONSTANT,
                severity=severity, message="test", metric_value=None,
            )
            result: list[Recommendation] = engine.generate([insight], _any_quality())
            assert result[0].priority == expected_priority, f"Failed for {severity}"

    def test_unknown_severity_defaults_to_priority_5(self) -> None:
        insight: Insight = Insight(
            column="c", category=InsightCategory.CONSTANT,
            severity=None, message="test", metric_value=None,  # type: ignore[arg-type]
        )
        engine: RecommendationEngine = RecommendationEngine()
        result: list[Recommendation] = engine.generate([insight], _any_quality())

        assert result[0].priority == 5
