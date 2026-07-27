from __future__ import annotations

"""Testes de borda para o motor de geração de insights.

Cobre branches não testados: total_column == 0, severidades CRITICAL
/ HIGH / MEDIUM / LOW para nulos/skewness/cardinalidade, colunas
quase-constantes, duplicatas HIGH/MEDIUM/LOW, outliers com/seção de
bounds, valores zero, violações de regras de negócio.
"""

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.domain.entities.quality_score import QualityDimension, QualityFactor, QualityScore
from spark_eda.domain.entities.statistic import (
    CategoricalStats,
    NumericStats,
)
from spark_eda.domain.services.insight_engine import InsightEngine
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.outlier_method import OutlierMethod
from spark_eda.domain.value_objects.severity import Severity


def _build_empty_quality_score() -> QualityScore:
    """Constrói um QualityScore neutro sem penalizadores para testes."""
    return QualityScore(
        overall=100.0,
        dimensions={},
        top_penalizers=[],
    )


def _build_quality_score_with_accuracy_factor(
    score: float,
    reason: str,
    affected_columns: list[str],
) -> QualityScore:
    """Constrói um QualityScore com um fator de acurácia (regras de negócio)."""
    factor: QualityFactor = QualityFactor(
        name="Regras de negócio",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=reason,
        severity=Severity.HIGH,
        affected_columns=affected_columns,
    )
    dimension: QualityDimension = QualityDimension(
        name="accuracy",
        score=score * 100.0,
        weight=0.20,
        contribution=score * 100.0 * 0.20,
        factors=[factor],
    )
    return QualityScore(
        overall=score * 100.0,
        dimensions={"accuracy": dimension},
        top_penalizers=[factor],
    )


class TestInsightEngineEdge:
    def test_null_ratio_between_30_and_40_medium(self) -> None:
        """null_ratio entre 30% e 40% → severidade MEDIUM (linha 60)."""
        metadata: ColumnMetadata = ColumnMetadata(
            name="opcional",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=35,
            non_null_count=65,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"A": 40, "B": 25},
            mode="A",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="med_null",
            columns=(metadata,),
            row_count=100,
            column_profiles={"opcional": profile},
        )
        engine: InsightEngine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        null_insights = [i for i in insights if i.category == InsightCategory.NULLS]
        assert len(null_insights) == 1
        assert null_insights[0].severity == Severity.MEDIUM

    def test_null_column_total_zero_skipped(self) -> None:
        """Coluna com null_count + non_null_count == 0 é ignorada (linha 50)."""
        metadata: ColumnMetadata = ColumnMetadata(
            name="vazia",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=0,
        )
        profile = ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="empty_col",
            columns=(metadata,),
            row_count=0,
            column_profiles={"vazia": profile},
        )
        engine: InsightEngine = InsightEngine()
        insights: list[Insight] = engine.generate(data_profile, _build_empty_quality_score())
        null_insights = [i for i in insights if i.category == InsightCategory.NULLS]
        assert len(null_insights) == 0

    def test_null_ratio_above_50_percent_critical(self) -> None:
        """null_ratio > 50% → severidade CRITICAL (linha 56)."""
        metadata: ColumnMetadata = ColumnMetadata(
            name="telefone",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=60,
            non_null_count=40,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"A": 20, "B": 20},
            mode="A",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="critical_null",
            columns=(metadata,),
            row_count=100,
            column_profiles={"telefone": profile},
        )
        engine: InsightEngine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        null_insights = [i for i in insights if i.category == InsightCategory.NULLS]
        assert len(null_insights) == 1
        assert null_insights[0].severity == Severity.CRITICAL

    def test_null_ratio_between_40_and_50_high(self) -> None:
        """null_ratio entre 40% e 50% → severidade HIGH (linha 58)."""
        metadata: ColumnMetadata = ColumnMetadata(
            name="obs",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=45,
            non_null_count=55,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"X": 30, "Y": 25},
            mode="X",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="high_null",
            columns=(metadata,),
            row_count=100,
            column_profiles={"obs": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        null_insights = [i for i in insights if i.category == InsightCategory.NULLS]
        assert len(null_insights) == 1
        assert null_insights[0].severity == Severity.HIGH

    def test_skewness_between_1_and_1_5_low(self) -> None:
        """|skewness| entre 1.0 e 1.5 → severidade LOW (linha 102)."""
        metadata: ColumnMetadata = ColumnMetadata(
            name="leve_assimetria",
            data_type=DataType.DOUBLE,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: NumericStats = NumericStats(
            mean=50.0,
            std=20.0,
            min=1.0,
            q25=35.0,
            q50=45.0,
            q75=60.0,
            max=150.0,
            skewness=1.2,
            kurtosis=3.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="low_skew",
            columns=(metadata,),
            row_count=100,
            column_profiles={"leve_assimetria": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        skew_insights = [i for i in insights if i.category == InsightCategory.SKEWNESS]
        assert len(skew_insights) == 1
        assert skew_insights[0].severity == Severity.LOW

    def test_skewness_above_2_high(self) -> None:
        """|skewness| > 2.0 → severidade HIGH (linha 98)."""
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
            skewness=2.5,
            kurtosis=10.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="high_skew",
            columns=(metadata,),
            row_count=100,
            column_profiles={"renda": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        skew_insights = [i for i in insights if i.category == InsightCategory.SKEWNESS]
        assert len(skew_insights) == 1
        assert skew_insights[0].severity == Severity.HIGH

    def test_skewness_between_1_5_and_2_medium(self) -> None:
        """|skewness| entre 1.5 e 2.0 → severidade MEDIUM (linha 100)."""
        metadata = ColumnMetadata(
            name="score",
            data_type=DataType.DOUBLE,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=50.0,
            std=20.0,
            min=1.0,
            q25=35.0,
            q50=45.0,
            q75=60.0,
            max=150.0,
            skewness=1.8,
            kurtosis=4.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="med_skew",
            columns=(metadata,),
            row_count=100,
            column_profiles={"score": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        skew_insights = [i for i in insights if i.category == InsightCategory.SKEWNESS]
        assert len(skew_insights) == 1
        assert skew_insights[0].severity == Severity.MEDIUM

    def test_cardinality_between_95_and_99_low(self) -> None:
        """unique_ratio entre 0.95 e 0.99 → severidade LOW (linha 140)."""
        metadata = ColumnMetadata(
            name="email",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = CategoricalStats(
            value_counts={f"u{i}": 1 for i in range(97)},
            mode="u1",
            cardinality=97,
            unique_ratio=0.97,
        )
        # adiciona 3 itens repetidos para totalizar 100 rows
        stats = CategoricalStats(
            value_counts={"a@a.com": 3} | {f"u{i}@a.com": 1 for i in range(97)},
            mode="a@a.com",
            cardinality=98,
            unique_ratio=0.98,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="card_low",
            columns=(metadata,),
            row_count=100,
            column_profiles={"email": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        card_insights = [i for i in insights if i.category == InsightCategory.CARDINALITY]
        assert len(card_insights) == 1
        assert card_insights[0].severity == Severity.LOW

    def test_near_constant_column_insight(self) -> None:
        """cardinalidade 2 com row_count > 100 → NEAR_CONSTANT (linha 187)."""
        metadata = ColumnMetadata(
            name="flag",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=200,
        )
        stats = CategoricalStats(
            value_counts={"S": 150, "N": 50},
            mode="S",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="near_const",
            columns=(metadata,),
            row_count=200,
            column_profiles={"flag": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        near_const = [i for i in insights if i.category == InsightCategory.NEAR_CONSTANT]
        assert len(near_const) == 1

    def test_duplicate_ratio_between_10_and_20_medium(self) -> None:
        """estimated_duplicate_ratio entre 10% e 20% → MEDIUM (linha 228)."""
        metadata = ColumnMetadata(
            name="cat_med",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = CategoricalStats(
            value_counts={f"v{i}": 1 for i in range(85)},
            mode="v1",
            cardinality=85,
            unique_ratio=0.85,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="med_dup",
            columns=(metadata,),
            row_count=100,
            column_profiles={"cat_med": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        dup_insights = [i for i in insights if i.category == InsightCategory.DUPLICATES]
        assert len(dup_insights) == 1
        assert dup_insights[0].severity == Severity.MEDIUM

    def test_duplicate_ratio_above_20_high(self) -> None:
        """estimated_duplicate_ratio > 20% → HIGH (linha 226)."""
        metadata = ColumnMetadata(
            name="cat",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = CategoricalStats(
            value_counts={"A": 60, "B": 30, "C": 10},
            mode="A",
            cardinality=3,
            unique_ratio=0.7,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="high_dup",
            columns=(metadata,),
            row_count=100,
            column_profiles={"cat": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        dup_insights = [i for i in insights if i.category == InsightCategory.DUPLICATES]
        assert len(dup_insights) == 1
        assert dup_insights[0].severity == Severity.HIGH

    def test_duplicate_ratio_below_10_low(self) -> None:
        """estimated_duplicate_ratio < 10% → LOW (linha 230)."""
        metadata = ColumnMetadata(
            name="cat",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = CategoricalStats(
            value_counts={f"v{i}": 1 for i in range(93)},
            mode="v1",
            cardinality=93,
            unique_ratio=0.93,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="low_dup",
            columns=(metadata,),
            row_count=100,
            column_profiles={"cat": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        dup_insights = [i for i in insights if i.category == InsightCategory.DUPLICATES]
        assert len(dup_insights) == 1
        assert dup_insights[0].severity == Severity.LOW

    def test_outlier_both_bounds(self) -> None:
        """Outlier com ambos os bounds definidos (linhas 272-277)."""
        metadata = ColumnMetadata(
            name="valor",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=50.0,
            std=15.0,
            min=0.0,
            q25=40.0,
            q50=50.0,
            q75=60.0,
            max=200.0,
            skewness=0.5,
            kurtosis=2.0,
        )
        outlier = OutlierInfo(
            method=OutlierMethod.IQR,
            count=15,
            ratio=0.15,
            bounds_lower=10.0,
            bounds_upper=90.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        data_profile = DataProfile(
            id="out_both_bounds",
            columns=(metadata,),
            row_count=100,
            column_profiles={"valor": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        out_insights = [i for i in insights if i.category == InsightCategory.OUTLIERS]
        assert len(out_insights) == 1
        assert "limites:" in out_insights[0].message
        assert "10" in out_insights[0].message
        assert "90" in out_insights[0].message

    def test_outlier_no_bounds(self) -> None:
        """Outlier com bounds None (linhas 272-277, sem bounds_info)."""
        metadata = ColumnMetadata(
            name="preco",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=100.0,
            std=30.0,
            min=10.0,
            q25=80.0,
            q50=95.0,
            q75=120.0,
            max=500.0,
            skewness=0.8,
            kurtosis=3.0,
        )
        outlier = OutlierInfo(
            method=OutlierMethod.ZSCORE,
            count=12,
            ratio=0.12,
            bounds_lower=None,
            bounds_upper=None,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        data_profile = DataProfile(
            id="out_no_bounds",
            columns=(metadata,),
            row_count=100,
            column_profiles={"preco": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        out_insights = [i for i in insights if i.category == InsightCategory.OUTLIERS]
        assert len(out_insights) == 1
        assert "limites" not in out_insights[0].message

    def test_outlier_ratio_above_25_high(self) -> None:
        """outlier.ratio > 0.25 → HIGH (linha 266)."""
        metadata = ColumnMetadata(
            name="alto",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=50.0,
            std=15.0,
            min=0.0,
            q25=40.0,
            q50=50.0,
            q75=60.0,
            max=500.0,
            skewness=0.5,
            kurtosis=2.0,
        )
        outlier = OutlierInfo(
            method=OutlierMethod.IQR,
            count=30,
            ratio=0.30,
            bounds_lower=5.0,
            bounds_upper=95.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        data_profile = DataProfile(
            id="out_high",
            columns=(metadata,),
            row_count=100,
            column_profiles={"alto": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        out_insights = [i for i in insights if i.category == InsightCategory.OUTLIERS]
        assert len(out_insights) == 1
        assert out_insights[0].severity == Severity.HIGH

    def test_outlier_ratio_between_15_and_25_medium(self) -> None:
        """outlier.ratio entre 0.15 e 0.25 → MEDIUM (linha 268)."""
        metadata = ColumnMetadata(
            name="medio",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=50.0,
            std=15.0,
            min=0.0,
            q25=40.0,
            q50=50.0,
            q75=60.0,
            max=300.0,
            skewness=0.5,
            kurtosis=2.0,
        )
        outlier = OutlierInfo(
            method=OutlierMethod.IQR,
            count=20,
            ratio=0.20,
            bounds_lower=5.0,
            bounds_upper=95.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        data_profile = DataProfile(
            id="out_medium",
            columns=(metadata,),
            row_count=100,
            column_profiles={"medio": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        out_insights = [i for i in insights if i.category == InsightCategory.OUTLIERS]
        assert len(out_insights) == 1
        assert out_insights[0].severity == Severity.MEDIUM

    def test_outlier_ratio_below_threshold_skipped(self) -> None:
        """outlier.ratio <= 10% → nenhum insight de outliers (linha 263->257)."""
        metadata = ColumnMetadata(
            name="pouco_out",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=50.0,
            std=15.0,
            min=10.0,
            q25=40.0,
            q50=50.0,
            q75=60.0,
            max=90.0,
            skewness=0.1,
            kurtosis=2.0,
        )
        outlier = OutlierInfo(
            method=OutlierMethod.IQR,
            count=5,
            ratio=0.05,
            bounds_lower=10.0,
            bounds_upper=90.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        data_profile = DataProfile(
            id="out_skip",
            columns=(metadata,),
            row_count=100,
            column_profiles={"pouco_out": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        out_insights = [i for i in insights if i.category == InsightCategory.OUTLIERS]
        assert len(out_insights) == 0

    def test_outlier_ratio_between_10_and_15_low(self) -> None:
        """outlier.ratio entre 0.10 e 0.15 → LOW (linha 270)."""
        metadata = ColumnMetadata(
            name="baixo",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=50.0,
            std=15.0,
            min=0.0,
            q25=40.0,
            q50=50.0,
            q75=60.0,
            max=200.0,
            skewness=0.5,
            kurtosis=2.0,
        )
        outlier = OutlierInfo(
            method=OutlierMethod.IQR,
            count=12,
            ratio=0.12,
            bounds_lower=5.0,
            bounds_upper=95.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=outlier)
        data_profile = DataProfile(
            id="out_low",
            columns=(metadata,),
            row_count=100,
            column_profiles={"baixo": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        out_insights = [i for i in insights if i.category == InsightCategory.OUTLIERS]
        assert len(out_insights) == 1
        assert out_insights[0].severity == Severity.LOW

    def test_zero_values_insight(self) -> None:
        """Coluna com nome contendo 'zero' e min == 0 → ZERO_VALUES (linha 314)."""
        metadata = ColumnMetadata(
            name="zerado_count",
            data_type=DataType.INTEGER,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=5.0,
            std=2.0,
            min=0.0,
            q25=3.0,
            q50=5.0,
            q75=7.0,
            max=10.0,
            skewness=0.0,
            kurtosis=-1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="zero_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"zerado_count": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, _build_empty_quality_score())
        zero_insights = [i for i in insights if i.category == InsightCategory.ZERO_VALUES]
        assert len(zero_insights) == 1

    def test_business_pattern_high_severity(self) -> None:
        """factor.score < 0.3 → HIGH (linha 348-349)."""
        metadata = ColumnMetadata(
            name="ano_ref",
            data_type=DataType.INTEGER,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=2000.0,
            std=1.0,
            min=1800.0,
            q25=1990.0,
            q50=2000.0,
            q75=2010.0,
            max=2020.0,
            skewness=0.0,
            kurtosis=-1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="biz_high",
            columns=(metadata,),
            row_count=100,
            column_profiles={"ano_ref": profile},
        )
        quality = _build_quality_score_with_accuracy_factor(
            score=0.2,
            reason="Ano fora do intervalo",
            affected_columns=["ano_ref"],
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, quality)
        biz_insights = [i for i in insights if i.category == InsightCategory.BUSINESS_PATTERN]
        assert len(biz_insights) >= 1
        biz_ano = [i for i in biz_insights if i.column == "ano_ref"]
        if biz_ano:
            assert biz_ano[0].severity == Severity.HIGH

    def test_business_pattern_medium_severity(self) -> None:
        """factor.score entre 0.3 e 0.6 → MEDIUM (linha 350-351)."""
        quality = _build_quality_score_with_accuracy_factor(
            score=0.5,
            reason="Valor inconsistente",
            affected_columns=["coluna_x"],
        )
        metadata = ColumnMetadata(
            name="coluna_x",
            data_type=DataType.INTEGER,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=10.0,
            std=2.0,
            min=1.0,
            q25=8.0,
            q50=10.0,
            q75=12.0,
            max=20.0,
            skewness=0.0,
            kurtosis=-1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="biz_med",
            columns=(metadata,),
            row_count=100,
            column_profiles={"coluna_x": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, quality)
        biz_insights = [i for i in insights if i.category == InsightCategory.BUSINESS_PATTERN]
        assert len(biz_insights) >= 1
        if biz_insights:
            assert biz_insights[0].severity == Severity.MEDIUM

    def test_business_pattern_low_severity(self) -> None:
        """factor.score >= 0.6 → LOW (linha 353)."""
        quality = _build_quality_score_with_accuracy_factor(
            score=0.8,
            reason="Pequena divergência",
            affected_columns=["coluna_y"],
        )
        metadata = ColumnMetadata(
            name="coluna_y",
            data_type=DataType.INTEGER,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=10.0,
            std=2.0,
            min=1.0,
            q25=8.0,
            q50=10.0,
            q75=12.0,
            max=20.0,
            skewness=0.0,
            kurtosis=-1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="biz_low",
            columns=(metadata,),
            row_count=100,
            column_profiles={"coluna_y": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, quality)
        biz_insights = [i for i in insights if i.category == InsightCategory.BUSINESS_PATTERN]
        assert len(biz_insights) >= 1
        if biz_insights:
            assert biz_insights[0].severity == Severity.LOW

    def test_business_pattern_factor_score_1_skipped(self) -> None:
        """factor.score == 1.0 → insight NÃO é gerado (linha 345->344)."""
        quality = _build_quality_score_with_accuracy_factor(
            score=1.0,
            reason="Tudo ok",
            affected_columns=["col_x"],
        )
        metadata = ColumnMetadata(
            name="col_x",
            data_type=DataType.INTEGER,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats = NumericStats(
            mean=10.0,
            std=2.0,
            min=1.0,
            q25=8.0,
            q50=10.0,
            q75=12.0,
            max=20.0,
            skewness=0.0,
            kurtosis=-1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="biz_skip",
            columns=(metadata,),
            row_count=100,
            column_profiles={"col_x": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, quality)
        biz_insights = [i for i in insights if i.category == InsightCategory.BUSINESS_PATTERN]
        assert len(biz_insights) == 0

    def test_business_pattern_no_accuracy_dimension(self) -> None:
        """Dimensão 'accuracy' ausente → sem insights (linha 341-342)."""
        quality = _build_empty_quality_score()
        metadata = ColumnMetadata(
            name="qualquer",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        stats = CategoricalStats(
            value_counts={"A": 10},
            mode="A",
            cardinality=1,
            unique_ratio=1.0,
        )
        profile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile = DataProfile(
            id="no_accuracy",
            columns=(metadata,),
            row_count=10,
            column_profiles={"qualquer": profile},
        )
        engine = InsightEngine()
        insights = engine.generate(data_profile, quality)
        biz_insights = [i for i in insights if i.category == InsightCategory.BUSINESS_PATTERN]
        assert len(biz_insights) == 0
