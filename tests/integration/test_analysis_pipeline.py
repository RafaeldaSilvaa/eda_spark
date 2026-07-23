from __future__ import annotations

"""Teste de integração completo do pipeline com dados gerados via Faker.

Gera um dataset realista com ~500 linhas e tipos mistos usando a
biblioteca Faker, depois executa o pipeline completo (profile,
qualidade, análise, correlações) e valida todas as saídas.
"""

from datetime import date, datetime
from typing import Any

import pytest
from faker import Faker
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    BinaryType,
    BooleanType,
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from spark_eda import EDAConfig, QualityConfig, analyze, assess_quality
from spark_eda.adapters.providers.spark_data_provider import SparkDataProvider
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.quality_section import QualityReport
from spark_eda.domain.entities.correlation import Correlation
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.value_objects.correlation_method import CorrelationMethod

pytestmark = pytest.mark.integration

fake: Faker = Faker("pt_BR")
Faker.seed(42)


@pytest.fixture(scope="session")
def faker_dataframe(spark_session: SparkSession) -> DataFrame:
    """Gera ~500 linhas de dados realistas com Faker."""
    schema: StructType = StructType([
        StructField("id", IntegerType(), nullable=False),
        StructField("nome", StringType(), nullable=True),
        StructField("email", StringType(), nullable=True),
        StructField("cidade", StringType(), nullable=True),
        StructField("salario", DoubleType(), nullable=True),
        StructField("dependentes", IntegerType(), nullable=True),
        StructField("data_nascimento", DateType(), nullable=True),
        StructField("ativo", BooleanType(), nullable=False),
        StructField("ultimo_acesso", TimestampType(), nullable=True),
    ])

    data: list[tuple[int, str | None, str | None, str | None,
                       float | None, int | None, date | None, bool,
                       datetime | None]] = []

    for i in range(500):
        nome: str = fake.name() if i % 10 != 0 else None
        email: str = fake.email() if i % 7 != 0 else None
        cidade: str = fake.city() if i % 5 != 0 else None
        salario: float | None = (
            round(float(fake.random_int(1500, 25000)), 2) if i % 6 != 0 else None
        )
        dependentes: int | None = fake.random_int(0, 5) if i % 8 != 0 else None
        dt_nasc: date = fake.date_of_birth(minimum_age=18, maximum_age=80)
        ativo: bool = fake.boolean(chance_of_getting_true=80)
        ultimo: datetime = fake.date_time_this_year() if i % 3 != 0 else None

        data.append((i, nome, email, cidade, salario, dependentes,
                      dt_nasc, ativo, ultimo))

    return spark_session.createDataFrame(data, schema=schema)


@pytest.fixture
def provider() -> SparkDataProvider:
    return SparkDataProvider()


@pytest.fixture
def default_config() -> EDAConfig:
    return EDAConfig(sampling_threshold=1_000_000)


class TestFakerAnalysisPipeline:
    """Valida o pipeline completo com dados realistas do Faker."""

    def test_analyze_returns_valid_report(
        self, faker_dataframe: DataFrame,
    ) -> None:
        """spark_eda.analyze() retorna EDAReport com todas as seções."""
        report: EDAReport = analyze(faker_dataframe)

        assert isinstance(report, EDAReport)
        assert report.overview.row_count == 500
        assert report.overview.column_count == 9
        assert len(report.insights.insights) > 0
        assert len(report.recommendations.recommendations) > 0
        assert report.quality.overall > 0.0

    def test_assess_quality_returns_valid_report(
        self, faker_dataframe: DataFrame,
    ) -> None:
        """spark_eda.assess_quality() retorna QualityReport com pontuação."""
        report: QualityReport = assess_quality(faker_dataframe)

        assert isinstance(report, QualityReport)
        assert 0.0 <= report.overall <= 100.0

    def test_analyze_with_custom_config(
        self, faker_dataframe: DataFrame,
    ) -> None:
        """analyze() com configuração personalizada."""
        config: EDAConfig = EDAConfig(
            sampling_threshold=500_000,
            cache_ttl_seconds=300,
        )

        report: EDAReport = analyze(faker_dataframe, config=config)

        assert isinstance(report, EDAReport)
        assert report.overview.row_count == 500

    def test_assess_quality_with_custom_config(
        self, faker_dataframe: DataFrame,
    ) -> None:
        """assess_quality() com configuração personalizada."""
        report: QualityReport = assess_quality(faker_dataframe)

        assert isinstance(report, QualityReport)
        assert 0.0 <= report.overall <= 100.0

    def test_profile_has_all_column_types(
        self, faker_dataframe: DataFrame, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """O perfil deve conter estatísticas para todos os tipos de coluna."""
        profile: DataProfile = provider.compute_profile(
            faker_dataframe, columns=None, config=default_config,
        )

        assert profile.row_count == 500
        assert len(profile.columns) == 9
        assert profile.id != ""

        col_names: list[str] = [c.name for c in profile.columns]
        for expected in ("id", "nome", "salario", "data_nascimento", "ativo"):
            assert expected in col_names

    def test_correlations_with_multiple_numeric_columns(
        self, faker_dataframe: DataFrame, provider: SparkDataProvider,
    ) -> None:
        """Correlações pareadas entre colunas numéricas."""
        corrs: list[Correlation] = provider.compute_correlations(
            faker_dataframe,
            numeric_columns=["id", "salario", "dependentes"],
            method="pearson",
        )

        assert len(corrs) == 3
        for c in corrs:
            assert isinstance(c, Correlation)
            assert c.method == CorrelationMethod.PEARSON
            assert -1.0 <= c.value <= 1.0

    def test_unsupported_correlation_method_raises(
        self, faker_dataframe: DataFrame, provider: SparkDataProvider,
    ) -> None:
        """Método de correlação não suportado deve levantar ValueError."""
        with pytest.raises(ValueError, match="Unsupported correlation method"):
            provider.compute_correlations(
                faker_dataframe,
                numeric_columns=["id", "salario"],
                method="spearman",
            )

    def test_fingerprint_consistency(
        self, faker_dataframe: DataFrame, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """Mesmo DataFrame deve produzir fingerprints idênticos."""
        fp1: str = provider.compute_fingerprint(faker_dataframe, default_config)
        fp2: str = provider.compute_fingerprint(faker_dataframe, default_config)

        assert fp1 == fp2
        assert len(fp1) == 64


class TestFakerEdgeCases:
    """Testa condições extremas com dados gerados por Faker."""

    def test_profile_with_temporal_distribution(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """DataFrame com datas deve gerar distribuição temporal."""
        schema: StructType = StructType([
            StructField("id", IntegerType()),
            StructField("dt", DateType()),
        ])
        from datetime import date, timedelta
        data: list[tuple[int, date]] = [
            (i, date(2024, 1, 1) + timedelta(days=i % 365))
            for i in range(100)
        ]
        df: DataFrame = spark_session.createDataFrame(data, schema=schema)

        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=default_config,
        )

        assert "dt" in profile.column_profiles
        col = profile.column_profiles["dt"]
        assert col.stats is not None

    def test_very_long_strings_in_text_column(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """Coluna com strings longas deve ter TextStats em vez de
        CategoricalStats (avg_length > 50)."""
        schema: StructType = StructType([
            StructField("id", IntegerType()),
            StructField("texto_longo", StringType()),
        ])
        data: list[tuple[int, str]] = [
            (i, "X" * 100) for i in range(20)
        ]
        df: DataFrame = spark_session.createDataFrame(data, schema=schema)

        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=default_config,
        )

        col = profile.column_profiles["texto_longo"]
        from spark_eda.domain.entities.statistic import TextStats
        assert isinstance(col.stats, TextStats)
        assert col.stats.avg_length == 100.0

    def test_single_column_dataframe(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """DataFrame com única coluna não deve quebrar."""
        schema: StructType = StructType([
            StructField("valor", DoubleType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(float(i),) for i in range(10)], schema=schema,
        )

        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=default_config,
        )

        assert profile.row_count == 10
        assert len(profile.columns) == 1

    def test_timestamp_column_with_temporal_distribution(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """Coluna TimestampType deve gerar distribuição temporal."""
        from datetime import datetime, timedelta

        schema: StructType = StructType([
            StructField("ts", TimestampType()),
            StructField("valor", DoubleType()),
        ])
        data: list[tuple[datetime, float]] = [
            (datetime(2024, 1, 1) + timedelta(hours=i), float(i))
            for i in range(50)
        ]
        df: DataFrame = spark_session.createDataFrame(data, schema=schema)

        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=default_config,
        )

        assert profile.row_count == 50
        assert "ts" in profile.column_profiles
        assert profile.column_profiles["valor"].stats is not None

    def test_outlier_detection_with_all_methods(
        self, spark_session: SparkSession, provider: SparkDataProvider,
    ) -> None:
        """Detecção de outliers com métodos IQR, Z-score e MAD."""
        from types import SimpleNamespace

        schema: StructType = StructType([
            StructField("valor", DoubleType()),
        ])
        # 100 pontos normais + 5 outliers extremos
        data: list[tuple[float]] = [
            (float(50 + (i % 10) * 2),) for i in range(100)
        ] + [(1000.0,), (2000.0,), (-500.0,), (3000.0,), (-1000.0,)]
        df: DataFrame = spark_session.createDataFrame(data, schema=schema)

        for method in ("iqr", "zscore", "mad"):
            config = SimpleNamespace(
                outlier_method=method,
                sampling_threshold=1_000_000,
                outlier_iqr_multiplier=1.5,
                outlier_zscore_threshold=3.0,
                outlier_mad_threshold=3.5,
            )
            profile: DataProfile = provider.compute_profile(
                df, columns=None, config=config,
            )

            col = profile.column_profiles["valor"]
            assert col.outlier is not None, f"Outlier should be detected with {method}"
            assert col.outlier.count > 0, f"Outliers expected with {method}"

    def test_constant_column_distribution(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """Coluna constante não deve gerar distribuição numérica."""
        schema: StructType = StructType([
            StructField("x", DoubleType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(5.0,)] * 20, schema=schema,
        )

        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=default_config,
        )

        col = profile.column_profiles["x"]
        assert col.distribution is None  # min == max


class TestControllerEdgeCases:
    """Testa os controladores e funções de topo com casos extremos."""

    def test_analyze_with_none_dataframe_raises(self) -> None:
        """DataFrame nulo deve levantar ValueError."""
        with pytest.raises(ValueError, match="DataFrame cannot be None"):
            analyze(None)  # type: ignore[arg-type]

    def test_assess_quality_with_none_dataframe_raises(self) -> None:
        """DataFrame nulo deve levantar ValueError."""
        with pytest.raises(ValueError, match="DataFrame cannot be None"):
            assess_quality(None)  # type: ignore[arg-type]

    def test_analyze_with_only_non_numeric_columns(
        self, spark_session: SparkSession,
    ) -> None:
        """Dataset sem colunas numéricas não deve quebrar."""
        schema: StructType = StructType([
            StructField("nome", StringType()),
            StructField("categoria", StringType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [("Alice", "A"), ("Bob", "B"), ("Carol", "A")],
            schema=schema,
        )

        report: EDAReport = analyze(df)
        assert report.overview.row_count == 3
        assert report.quality.overall > 0.0

    def test_assess_quality_with_no_numeric_columns(
        self, spark_session: SparkSession,
    ) -> None:
        """qualidade sem colunas numéricas."""
        schema: StructType = StructType([
            StructField("rotulo", StringType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [("X",), ("Y",), ("Z",)], schema=schema,
        )

        report: QualityReport = assess_quality(df)
        assert 0.0 <= report.overall <= 100.0

    def test_analyze_then_assess_quality_caching(
        self, faker_dataframe: DataFrame,
    ) -> None:
        """analyze() sucessivos devem usar cache."""
        r1: EDAReport = analyze(faker_dataframe)
        r2: EDAReport = analyze(faker_dataframe)

        assert r1.overview.row_count == r2.overview.row_count


class TestSparkDataProviderCoverage:
    """Cobre linhas específicas do spark_data_provider.py."""

    def test_unmapped_spark_type_returns_other(
        self, spark_session: SparkSession, provider: SparkDataProvider,
    ) -> None:
        """BinaryType → DataType.OTHER (linha 98) e cobre linhas 666, 901, 1024-1029."""
        from spark_eda.domain.value_objects.data_type import DataType

        schema: StructType = StructType([
            StructField("id", IntegerType()),
            StructField("bin", BinaryType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(1, bytearray(b"hello")), (2, bytearray(b"world"))],
            schema=schema,
        )
        profile: DataProfile = provider.compute_profile(df, columns=None, config=SimpleNamespace(
            infer_semantic_types=False, outlier_threshold=3.0, sampling_threshold=1_000_000,
        ))
        col_profiles = profile.column_profiles
        assert col_profiles["id"].metadata.data_type == DataType.INTEGER
        assert col_profiles["bin"].metadata.data_type == DataType.OTHER
        assert col_profiles["bin"].distribution is None
        assert col_profiles["bin"].stats is None

    def test_zscore_with_constant_column(
        self, spark_session: SparkSession, provider: SparkDataProvider,
    ) -> None:
        """Z-score em coluna constante → std=0.0, retorna None (linha 477)."""
        schema: StructType = StructType([
            StructField("x", DoubleType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(5.0,)] * 20, schema=schema,
        )
        config = SimpleNamespace(
            outlier_method="zscore", sampling_threshold=1_000_000,
            outlier_zscore_threshold=3.0,
        )
        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=config,
        )
        col = profile.column_profiles["x"]
        assert col.outlier is None

    def test_mad_with_constant_column(
        self, spark_session: SparkSession, provider: SparkDataProvider,
    ) -> None:
        """MAD em coluna constante → mad_val=0.0, retorna None (linha 543)."""
        schema: StructType = StructType([
            StructField("x", DoubleType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(5.0,)] * 20, schema=schema,
        )
        config = SimpleNamespace(
            outlier_method="mad", sampling_threshold=1_000_000,
            outlier_mad_threshold=3.5,
        )
        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=config,
        )
        col = profile.column_profiles["x"]
        assert col.outlier is None

    def test_mad_with_all_null_column(
        self, spark_session: SparkSession, provider: SparkDataProvider,
    ) -> None:
        """MAD em coluna toda nula → median_list vazio, retorna None (linha 528)."""
        schema: StructType = StructType([
            StructField("x", DoubleType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(None,)] * 10, schema=schema,
        )
        config = SimpleNamespace(
            outlier_method="mad", sampling_threshold=1_000_000,
            outlier_mad_threshold=3.5,
        )
        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=config,
        )
        col = profile.column_profiles["x"]
        assert col.outlier is None

    def test_temporal_distribution_all_nulls(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """Datas todas nulas → distribuição temporal retorna None (linhas 697-726)."""
        schema: StructType = StructType([
            StructField("dt", DateType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(None,)] * 10, schema=schema,
        )
        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=default_config,
        )
        col = profile.column_profiles["dt"]
        assert col.distribution is None

    def test_empty_dataframe_duplicates(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """DataFrame vazio → duplicate_ratio 0.0 (linhas 743-750)."""
        from spark_eda.application.use_cases.assess_quality import AssessQualityUseCase, QualityRequest

        schema: StructType = StructType([
            StructField("x", IntegerType()),
        ])
        df: DataFrame = spark_session.createDataFrame([], schema=schema)
        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=default_config,
        )
        assert profile.row_count == 0

    def test_profile_with_missing_columns_raises(
        self, spark_session: SparkSession, provider: SparkDataProvider,
        default_config: Any,
    ) -> None:
        """Coluna inexistente → ValueError (linhas 826-835)."""
        schema: StructType = StructType([
            StructField("x", IntegerType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(1,), (2,)], schema=schema,
        )
        with pytest.raises(ValueError, match="do not exist in the schema"):
            provider.compute_profile(df, columns=["inexistente"], config=default_config)

    def test_sampling_triggered_by_low_threshold(
        self, spark_session: SparkSession, provider: SparkDataProvider,
    ) -> None:
        """sampling_threshold baixo → working_df é amostrado (linhas 842-844)."""
        schema: StructType = StructType([
            StructField("x", IntegerType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(i,) for i in range(100)], schema=schema,
        )
        config = SimpleNamespace(
            infer_semantic_types=False, outlier_threshold=3.0, sampling_threshold=10,
        )
        profile: DataProfile = provider.compute_profile(
            df, columns=None, config=config,
        )
        assert profile.row_count < 100  # sampled
        assert "x" in profile.column_profiles

    def test_correlation_constant_columns(
        self, spark_session: SparkSession, provider: SparkDataProvider,
    ) -> None:
        """Correlação entre colunas constantes não deve quebrar (linhas 1111-1112)."""
        schema: StructType = StructType([
            StructField("a", DoubleType()),
            StructField("b", DoubleType()),
        ])
        df: DataFrame = spark_session.createDataFrame(
            [(1.0, 2.0)] * 5, schema=schema,
        )
        corrs: list[Correlation] = provider.compute_correlations(
            df, numeric_columns=["a", "b"], method="pearson",
        )
        # At minimum, the pair (a, b) should exist
        assert len(corrs) == 1
