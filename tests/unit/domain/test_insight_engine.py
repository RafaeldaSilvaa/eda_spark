from __future__ import annotations

"""Testes para o motor de geração de insights.

Testa o serviço InsightEngine com perfis criados diretamente,
verificando as regras de negócio de cada categoria de insight.
"""

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.quality_score import QualityFactor, QualityDimension, QualityScore
from spark_eda.domain.entities.statistic import (
    CategoricalStats,
    NumericStats,
)
from spark_eda.domain.services.insight_engine import InsightEngine
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.severity import Severity


def _build_empty_quality_score() -> QualityScore:
    """Constrói um QualityScore neutro sem penalizadores para testes."""
    return QualityScore(
        overall=100.0,
        dimensions={},
        top_penalizers=[],
    )


class TestInsightEngine:
    """Testes para o motor de geração de insights."""

    def test_high_null_ratio_generates_null_insight(self) -> None:
        """Uma coluna com 40% de valores nulos deve gerar um insight da
        categoria NULLS.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="telefone",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=40,
            non_null_count=60,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"A": 30, "B": 30},
            mode="A",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="null_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"telefone": profile},
        )

        engine: InsightEngine = InsightEngine()
        insights: list[Insight] = engine.generate(data_profile, _build_empty_quality_score())

        null_insights: list[Insight] = [i for i in insights if i.category == InsightCategory.NULLS]
        assert len(null_insights) == 1
        assert null_insights[0].column == "telefone"
        assert null_insights[0].severity in (Severity.HIGH, Severity.MEDIUM)

    def test_high_skewness_generates_skewness_insight(self) -> None:
        """Uma coluna numérica com skewness > 1.0 deve gerar um insight da
        categoria SKEWNESS.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="renda",
            data_type=DataType.DOUBLE,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: NumericStats = NumericStats(
            mean=5000.0,
            std=3000.0,
            min=0.0,
            q25=2000.0,
            q50=4000.0,
            q75=7000.0,
            max=50000.0,
            skewness=1.5,
            kurtosis=3.0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="skewness_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"renda": profile},
        )

        engine: InsightEngine = InsightEngine()
        quality: QualityScore = _build_empty_quality_score()
        insights: list[Insight] = engine.generate(data_profile, quality)

        skew_insights: list[Insight] = [i for i in insights if i.category == InsightCategory.SKEWNESS]
        assert len(skew_insights) == 1
        assert skew_insights[0].column == "renda"
        assert abs(skew_insights[0].metric_value) >= 1.0  # type: ignore[operator]

    def test_constant_column_generates_constant_insight(self) -> None:
        """Uma coluna categórica com cardinalidade 1 deve gerar um insight
        da categoria CONSTANT.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="pais",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"Brasil": 100},
            mode="Brasil",
            cardinality=1,
            unique_ratio=1.0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="constant_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"pais": profile},
        )

        engine: InsightEngine = InsightEngine()
        insights: list[Insight] = engine.generate(data_profile, _build_empty_quality_score())

        constant_insights: list[Insight] = [
            i for i in insights if i.category == InsightCategory.CONSTANT
        ]
        assert len(constant_insights) == 1
        assert constant_insights[0].column == "pais"

    def test_duplicate_rows_generates_duplicate_insight(self) -> None:
        """Um perfil com taxa estimada de duplicatas > 5% deve gerar um
        insight da categoria DUPLICATES.
        """
        metadata_a: ColumnMetadata = ColumnMetadata(
            name="categoria",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        metadata_b: ColumnMetadata = ColumnMetadata(
            name="grupo",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats_a: CategoricalStats = CategoricalStats(
            value_counts={"A": 60, "B": 30, "C": 10},
            mode="A",
            cardinality=3,
            unique_ratio=0.9,
        )
        stats_b: CategoricalStats = CategoricalStats(
            value_counts={"X": 50, "Y": 30, "Z": 20},
            mode="X",
            cardinality=3,
            unique_ratio=0.8,
        )
        profile_a: ColumnProfile = ColumnProfile(metadata=metadata_a, stats=stats_a, distribution=None, outlier=None)
        profile_b: ColumnProfile = ColumnProfile(metadata=metadata_b, stats=stats_b, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="dup_test",
            columns=(metadata_a, metadata_b),
            row_count=100,
            column_profiles={"categoria": profile_a, "grupo": profile_b},
        )

        engine: InsightEngine = InsightEngine()
        insights: list[Insight] = engine.generate(data_profile, _build_empty_quality_score())

        dup_insights: list[Insight] = [
            i for i in insights if i.category == InsightCategory.DUPLICATES
        ]
        assert len(dup_insights) == 1
        assert dup_insights[0].column is None

    def test_perfect_data_generates_no_insights(self) -> None:
        """Um perfil de dados perfeito (sem nulos, sem assimetria, sem
        constantes, sem duplicatas) não deve gerar nenhum insight.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="idade",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: NumericStats = NumericStats(
            mean=35.0,
            std=10.0,
            min=18.0,
            q25=25.0,
            q50=33.0,
            q75=42.0,
            max=65.0,
            skewness=0.0,
            kurtosis=-1.0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="perfect",
            columns=(metadata,),
            row_count=100,
            column_profiles={"idade": profile},
        )

        engine: InsightEngine = InsightEngine()
        insights: list[Insight] = engine.generate(data_profile, _build_empty_quality_score())

        assert len(insights) == 0
