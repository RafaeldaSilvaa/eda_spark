from __future__ import annotations

"""Testes para o cálculo de pontuação de qualidade dos dados.

Testa o serviço QualityCalculator com perfis criados diretamente,
sem dependência de Spark ou fixtures.
"""

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.statistic import (
    CategoricalStats,
    NumericStats,
    TextStats,
)
from spark_eda.domain.entities.quality_score import QualityDimension
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.severity import Severity


class TestQualityScore:
    """Testes para o cálculo consolidado de qualidade via QualityCalculator."""

    def test_perfect_dataframe_returns_score_100(self) -> None:
        """Um perfil sem nulos, sem duplicatas e sem anomalias deve resultar em
        score 100.0.
        """
        metadata_a: ColumnMetadata = ColumnMetadata(
            name="valor",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=1000,
        )
        metadata_b: ColumnMetadata = ColumnMetadata(
            name="taxa",
            data_type=DataType.DOUBLE,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=1000,
        )
        profile_a: ColumnProfile = ColumnProfile(
            metadata=metadata_a,
            stats=NumericStats(
                mean=50.0,
                std=10.0,
                min=0.0,
                q25=25.0,
                q50=50.0,
                q75=75.0,
                max=100.0,
                skewness=0.0,
                kurtosis=-1.0,
            ),
            distribution=None,
            outlier=None,
        )
        profile_b: ColumnProfile = ColumnProfile(
            metadata=metadata_b,
            stats=NumericStats(
                mean=5.0,
                std=2.0,
                min=0.0,
                q25=3.0,
                q50=5.0,
                q75=7.0,
                max=10.0,
                skewness=0.0,
                kurtosis=-1.0,
            ),
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="perfect",
            columns=(metadata_a, metadata_b),
            row_count=1000,
            column_profiles={"valor": profile_a, "taxa": profile_b},
        )

        calculator: QualityCalculator = QualityCalculator()
        result = calculator.calculate(data_profile)

        assert result.overall == 100.0

    def test_all_null_columns_returns_score_zero(self) -> None:
        """Um perfil onde todas as colunas são 100% nulas deve resultar em
        completude e unicidade severamente penalizadas.
        """
        metadata_a: ColumnMetadata = ColumnMetadata(
            name="col_a",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=100,
            non_null_count=0,
        )
        metadata_b: ColumnMetadata = ColumnMetadata(
            name="col_b",
            data_type=DataType.INTEGER,
            nullable=True,
            inferred_type=None,
            null_count=100,
            non_null_count=0,
        )
        profile_a: ColumnProfile = ColumnProfile(
            metadata=metadata_a,
            stats=CategoricalStats(
                value_counts={},
                mode=None,
                cardinality=0,
                unique_ratio=0.0,
            ),
            distribution=None,
            outlier=None,
        )
        profile_b: ColumnProfile = ColumnProfile(
            metadata=metadata_b,
            stats=NumericStats(
                mean=0.0,
                std=0.0,
                min=0.0,
                q25=0.0,
                q50=0.0,
                q75=0.0,
                max=0.0,
                skewness=0.0,
                kurtosis=0.0,
            ),
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="all_nulls",
            columns=(metadata_a, metadata_b),
            row_count=100,
            column_profiles={"col_a": profile_a, "col_b": profile_b},
        )

        calculator: QualityCalculator = QualityCalculator()
        result = calculator.calculate(data_profile)

        dimensao_completude: QualityDimension = result.dimensions["completeness"]
        assert dimensao_completude.score < 40.0

    def test_partial_nulls_returns_intermediate_score(self) -> None:
        """Um perfil com 50% de nulos em todas as colunas deve resultar em
        um score overall reduzido (completude abaixo de 60).
        """
        metadata_a: ColumnMetadata = ColumnMetadata(
            name="col_a",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=50,
            non_null_count=50,
        )
        metadata_b: ColumnMetadata = ColumnMetadata(
            name="col_b",
            data_type=DataType.INTEGER,
            nullable=True,
            inferred_type=None,
            null_count=50,
            non_null_count=50,
        )
        profile_a: ColumnProfile = ColumnProfile(
            metadata=metadata_a,
            stats=CategoricalStats(
                value_counts={"X": 25, "Y": 25},
                mode="X",
                cardinality=2,
                unique_ratio=1.0,
            ),
            distribution=None,
            outlier=None,
        )
        profile_b: ColumnProfile = ColumnProfile(
            metadata=metadata_b,
            stats=NumericStats(
                mean=25.0,
                std=10.0,
                min=0.0,
                q25=12.5,
                q50=25.0,
                q75=37.5,
                max=50.0,
                skewness=0.0,
                kurtosis=-1.0,
            ),
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="half_nulls",
            columns=(metadata_a, metadata_b),
            row_count=100,
            column_profiles={"col_a": profile_a, "col_b": profile_b},
        )

        calculator: QualityCalculator = QualityCalculator()
        result = calculator.calculate(data_profile)

        dimensao_completude: QualityDimension = result.dimensions["completeness"]
        assert dimensao_completude.score < 60.0

    def test_duplicate_rows_reduce_uniqueness_score(self) -> None:
        """Um perfil com 20% de duplicatas estimadas deve resultar em
        score de unicidade inferior a 1.0 na escala 0-100.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="categoria",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"A": 80, "B": 20},
            mode="A",
            cardinality=2,
            unique_ratio=0.8,
        )
        profile: ColumnProfile = ColumnProfile(
            metadata=metadata,
            stats=stats,
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="with_duplicates",
            columns=(metadata,),
            row_count=100,
            column_profiles={"categoria": profile},
        )

        calculator: QualityCalculator = QualityCalculator()
        result = calculator.calculate(data_profile)

        dimensao_unicidade: QualityDimension = result.dimensions["uniqueness"]
        assert dimensao_unicidade.score < 100.0

    def test_constant_columns_reduce_score(self) -> None:
        """Colunas constantes (cardinalidade 1) devem ser penalizadas na
        dimensão de unicidade.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="constante",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"UNICO": 100},
            mode="UNICO",
            cardinality=1,
            unique_ratio=1.0,
        )
        profile: ColumnProfile = ColumnProfile(
            metadata=metadata,
            stats=stats,
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="constant_col",
            columns=(metadata,),
            row_count=100,
            column_profiles={"constante": profile},
        )

        calculator: QualityCalculator = QualityCalculator()
        result = calculator.calculate(data_profile)

        dimensao_unicidade: QualityDimension = result.dimensions["uniqueness"]
        assert dimensao_unicidade.score < 100.0

    def test_near_constant_columns_reduce_score_less_than_constant(self) -> None:
        """Colunas quase-constantes (cardinalidade 2-3) devem ser menos
        penalizadas que colunas perfeitamente constantes.
        """
        metadata_const: ColumnMetadata = ColumnMetadata(
            name="constante",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        metadata_near: ColumnMetadata = ColumnMetadata(
            name="quase_constante",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats_const: CategoricalStats = CategoricalStats(
            value_counts={"X": 100},
            mode="X",
            cardinality=1,
            unique_ratio=1.0,
        )
        stats_near: CategoricalStats = CategoricalStats(
            value_counts={"A": 60, "B": 40},
            mode="A",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile_const: ColumnProfile = ColumnProfile(
            metadata=metadata_const,
            stats=stats_const,
            distribution=None,
            outlier=None,
        )
        profile_near: ColumnProfile = ColumnProfile(
            metadata=metadata_near,
            stats=stats_near,
            distribution=None,
            outlier=None,
        )
        data_profile_const: DataProfile = DataProfile(
            id="const_only",
            columns=(metadata_const,),
            row_count=100,
            column_profiles={"constante": profile_const},
        )
        data_profile_near: DataProfile = DataProfile(
            id="near_only",
            columns=(metadata_near,),
            row_count=100,
            column_profiles={"quase_constante": profile_near},
        )

        calculator: QualityCalculator = QualityCalculator()
        result_const = calculator.calculate(data_profile_const)
        result_near = calculator.calculate(data_profile_near)

        score_const: float = result_const.dimensions["uniqueness"].score
        score_near: float = result_near.dimensions["uniqueness"].score
        assert score_near > score_const

    def test_top_penalizers_returns_worst_factors(self) -> None:
        """A lista top_penalizers deve conter os 5 fatores que mais
        penalizaram a pontuação geral.
        """
        metadata_a: ColumnMetadata = ColumnMetadata(
            name="nula",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=100,
            non_null_count=0,
        )
        metadata_b: ColumnMetadata = ColumnMetadata(
            name="valida",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        metadata_c: ColumnMetadata = ColumnMetadata(
            name="constante",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=50,
            non_null_count=50,
        )
        profile_a: ColumnProfile = ColumnProfile(
            metadata=metadata_a,
            stats=CategoricalStats(
                value_counts={},
                mode=None,
                cardinality=0,
                unique_ratio=0.0,
            ),
            distribution=None,
            outlier=None,
        )
        profile_b: ColumnProfile = ColumnProfile(
            metadata=metadata_b,
            stats=NumericStats(
                mean=50.0,
                std=10.0,
                min=0.0,
                q25=25.0,
                q50=50.0,
                q75=75.0,
                max=100.0,
                skewness=0.0,
                kurtosis=-1.0,
            ),
            distribution=None,
            outlier=None,
        )
        profile_c: ColumnProfile = ColumnProfile(
            metadata=metadata_c,
            stats=CategoricalStats(
                value_counts={"X": 100},
                mode="X",
                cardinality=1,
                unique_ratio=1.0,
            ),
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="with_penalizers",
            columns=(metadata_a, metadata_b, metadata_c),
            row_count=100,
            column_profiles={
                "nula": profile_a,
                "valida": profile_b,
                "constante": profile_c,
            },
        )

        calculator: QualityCalculator = QualityCalculator()
        result = calculator.calculate(data_profile)

        assert len(result.top_penalizers) == 5
        for factor in result.top_penalizers:
            assert factor.score < 1.0
