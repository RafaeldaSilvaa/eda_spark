from __future__ import annotations

"""Testes individuais para as funções de fator de qualidade.

Testa cada função de scoring registrada no FACTOR_REGISTRY com perfis
construídos diretamente, sem dependência de Spark.
"""

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.statistic import (
    CategoricalStats,
    NumericStats,
    TextStats,
    TemporalStats,
)
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.services.quality_factors import FACTOR_REGISTRY
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.severity import Severity


class TestCompletenessFactors:
    """Testes para os fatores da dimensão Completude."""

    def test_completeness_non_null_ratio_score(self) -> None:
        """Uma coluna com 90% de valores não nulos deve resultar em score
        de completude proporcional.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="nome",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=10,
            non_null_count=90,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"A": 45, "B": 45},
            mode="A",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="completeness_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"nome": profile},
        )

        factors: list[QualityFactor] = FACTOR_REGISTRY["completeness"](data_profile)

        non_null_factor: QualityFactor = next(
            f for f in factors if f.name == "Proporção de valores não nulos"
        )
        assert 0.85 <= non_null_factor.score <= 0.95

    def test_completeness_empty_strings_score(self) -> None:
        """Strings vazias em 5% dos registros de uma coluna textual devem
        produzir score > 0.9 no fator de strings vazias.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="descricao",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: TextStats = TextStats(
            min_length=0,
            max_length=200,
            avg_length=100.0,
            empty_ratio=0.05,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="empty_strings_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"descricao": profile},
        )

        factors: list[QualityFactor] = FACTOR_REGISTRY["completeness"](data_profile)

        empty_factor: QualityFactor = next(
            f for f in factors if f.name == "Proporção de strings vazias"
        )
        assert empty_factor.score > 0.9


class TestUniquenessFactors:
    """Testes para os fatores da dimensão Unicidade."""

    def test_uniqueness_duplicate_ratio_score(self) -> None:
        """Colunas categóricas com unique_ratio médio de 0.9 (10%
        duplicatas) devem produzir score < 1.0 no fator de duplicatas.
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
            value_counts={"A": 50, "B": 40, "C": 10},
            mode="A",
            cardinality=3,
            unique_ratio=0.9,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="uniqueness_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"categoria": profile},
        )

        factors: list[QualityFactor] = FACTOR_REGISTRY["uniqueness"](data_profile)

        dup_factor: QualityFactor = next(
            f for f in factors if f.name == "Proporção de duplicatas"
        )
        assert dup_factor.score < 1.0
        assert dup_factor.score > 0.0

    def test_uniqueness_near_constant_score(self) -> None:
        """Uma coluna quase-constante (cardinalidade 2 em 1000 linhas) deve
        ser penalizada no fator de colunas quase-constantes.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="flag",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=1000,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"S": 600, "N": 400},
            mode="S",
            cardinality=2,
            unique_ratio=1.0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="near_constant_test",
            columns=(metadata,),
            row_count=1000,
            column_profiles={"flag": profile},
        )

        factors: list[QualityFactor] = FACTOR_REGISTRY["uniqueness"](data_profile)

        near_const_factor: QualityFactor = next(
            f for f in factors if f.name == "Colunas quase-constantes"
        )
        assert near_const_factor.score < 1.0


class TestConsistencyFactors:
    """Testes para os fatores da dimensão Consistência."""

    def test_consistency_type_mismatch_score(self) -> None:
        """Colunas com tipo declarado incompatível com as estatísticas
        disponíveis devem resultar em score de consistência de tipos
        inferior a 1.0.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="data_ref",
            data_type=DataType.DATE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: CategoricalStats = CategoricalStats(
            value_counts={"2024-01-01": 100},
            mode="2024-01-01",
            cardinality=1,
            unique_ratio=1.0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="type_mismatch_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"data_ref": profile},
        )

        factors: list[QualityFactor] = FACTOR_REGISTRY["consistency"](data_profile)

        type_factor: QualityFactor = next(
            f for f in factors if f.name == "Consistência de tipos"
        )
        assert type_factor.score < 1.0


class TestTimelinessFactors:
    """Testes para os fatores da dimensão Atualidade."""

    def test_timeliness_invalid_dates_score(self) -> None:
        """Colunas temporais com alta proporção de valores nulos (proxy
        para datas inválidas) devem resultar em score < 1.0 no fator de
        datas inválidas.
        """
        metadata: ColumnMetadata = ColumnMetadata(
            name="data_evento",
            data_type=DataType.DATE,
            nullable=True,
            inferred_type=None,
            null_count=30,
            non_null_count=70,
        )
        temporal_stats: TemporalStats = TemporalStats(
            min_date="2024-01-01",
            max_date="2024-12-31",
            range_days=365,
            gap_count=0,
        )
        profile: ColumnProfile = ColumnProfile(metadata=metadata, stats=temporal_stats, distribution=None, outlier=None)
        data_profile: DataProfile = DataProfile(
            id="invalid_dates_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"data_evento": profile},
        )

        factors: list[QualityFactor] = FACTOR_REGISTRY["timeliness"](data_profile)

        invalid_dates_factor: QualityFactor = next(
            f for f in factors if f.name == "Datas inválidas"
        )
        assert invalid_dates_factor.score < 1.0


class TestAccuracyFactors:
    """Testes para os fatores da dimensão Acurácia."""

    def test_accuracy_outlier_ratio_score(self) -> None:
        """Colunas com outliers presentes devem resultar em score de
        proporção de outliers inferior a 1.0.
        """
        from spark_eda.domain.entities.outlier import OutlierInfo
        from spark_eda.domain.value_objects.outlier_method import OutlierMethod

        metadata: ColumnMetadata = ColumnMetadata(
            name="valor",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        numeric_stats: NumericStats = NumericStats(
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
        outlier_info: OutlierInfo = OutlierInfo(
            method=OutlierMethod.IQR,
            count=10,
            ratio=0.10,
            bounds_lower=10.0,
            bounds_upper=90.0,
        )
        profile: ColumnProfile = ColumnProfile(
            metadata=metadata,
            stats=numeric_stats,
            distribution=None,
            outlier=outlier_info,
        )
        data_profile: DataProfile = DataProfile(
            id="outlier_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"valor": profile},
        )

        factors: list[QualityFactor] = FACTOR_REGISTRY["accuracy"](data_profile)

        outlier_factor: QualityFactor = next(
            f for f in factors if f.name == "Proporção de outliers"
        )
        assert outlier_factor.score < 1.0
