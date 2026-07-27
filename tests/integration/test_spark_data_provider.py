from __future__ import annotations

"""Testes de integração para o :class:`SparkDataProvider`.

Testa o fluxo completo de perfilamento de DataFrames PySpark,
incluindo detecção de nulos, estatísticas numéricas,
DataFrames vazios e fingerprints.
"""

from types import SimpleNamespace

import pytest
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from spark_eda.adapters.providers.spark_data_provider import SparkDataProvider
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.statistic import NumericStats

pytestmark = pytest.mark.integration


class TestSparkDataProvider:
    """Suite de testes de integração para o SparkDataProvider."""

    @pytest.fixture
    def provider(self) -> SparkDataProvider:
        """Fixture que retorna uma instância limpa do provedor."""
        return SparkDataProvider()

    @pytest.fixture
    def default_config(self) -> SimpleNamespace:
        """Fixture com configuração padrão para os testes."""
        return SimpleNamespace(
            infer_semantic_types=False,
            outlier_iqr_multiplier=1.5,
        )

    # ------------------------------------------------------------------
    # test_compute_profile_returns_data_profile
    # ------------------------------------------------------------------

    def test_compute_profile_returns_data_profile(
        self,
        provider: SparkDataProvider,
        sample_dataframe: DataFrame,
        default_config: SimpleNamespace,
    ) -> None:
        """Verifica que :meth:`compute_profile` retorna um :class:`DataProfile`."""
        # Arrange
        ...

        # Act
        profile: DataProfile = provider.compute_profile(
            dataframe=sample_dataframe,
            columns=None,
            config=default_config,
        )

        # Assert
        assert isinstance(profile, DataProfile)

    # ------------------------------------------------------------------
    # test_compute_profile_correct_row_count
    # ------------------------------------------------------------------

    def test_compute_profile_correct_row_count(
        self,
        provider: SparkDataProvider,
        spark_session: SparkSession,
        default_config: SimpleNamespace,
    ) -> None:
        """Verifica que o perfil retorna a contagem correta de linhas."""
        # Arrange
        expected_row_count: int = 100
        schema: StructType = StructType(
            [
                StructField("id", IntegerType(), nullable=False),
                StructField("nome", StringType(), nullable=True),
            ],
        )
        data: list[tuple[int, str]] = [(i, f"item_{i}") for i in range(expected_row_count)]
        dataframe: DataFrame = spark_session.createDataFrame(data, schema=schema)

        # Act
        profile: DataProfile = provider.compute_profile(
            dataframe=dataframe,
            columns=None,
            config=default_config,
        )

        # Assert
        assert profile.row_count == expected_row_count

    # ------------------------------------------------------------------
    # test_compute_profile_detects_nulls
    # ------------------------------------------------------------------

    def test_compute_profile_detects_nulls(
        self,
        provider: SparkDataProvider,
        null_dataframe: DataFrame,
        default_config: SimpleNamespace,
    ) -> None:
        """Verifica que colunas nulas são detectadas com null_count > 0."""
        # Arrange
        ...

        # Act
        profile: DataProfile = provider.compute_profile(
            dataframe=null_dataframe,
            columns=None,
            config=default_config,
        )

        # Assert
        for column_metadata in profile.columns:
            assert column_metadata.null_count > 0, f"A coluna {column_metadata.name} deveria ter nulos detectados."

    # ------------------------------------------------------------------
    # test_compute_profile_numeric_stats
    # ------------------------------------------------------------------

    def test_compute_profile_numeric_stats(
        self,
        provider: SparkDataProvider,
        clean_dataframe: DataFrame,
        default_config: SimpleNamespace,
    ) -> None:
        """Verifica que colunas numéricas possuem média, std, min e max."""
        # Arrange
        ...

        # Act
        profile: DataProfile = provider.compute_profile(
            dataframe=clean_dataframe,
            columns=None,
            config=default_config,
        )

        # Assert
        coluna_altura_profile: ColumnProfile = profile.column_profiles["altura"]
        stats = coluna_altura_profile.stats
        assert isinstance(stats, NumericStats), "Esperava-se NumericStats para a coluna 'altura'."
        assert stats.mean > 0.0
        assert stats.std > 0.0
        assert stats.min >= 0.0
        assert stats.max > stats.min

    # ------------------------------------------------------------------
    # test_empty_dataframe_does_not_crash
    # ------------------------------------------------------------------

    def test_empty_dataframe_does_not_crash(
        self,
        provider: SparkDataProvider,
        spark_session: SparkSession,
        default_config: SimpleNamespace,
    ) -> None:
        """Verifica que um DataFrame vazio produz um perfil válido sem lançar exceção."""
        # Arrange
        schema: StructType = StructType(
            [
                StructField("col_a", IntegerType(), nullable=True),
                StructField("col_b", StringType(), nullable=True),
            ],
        )
        empty_dataframe: DataFrame = spark_session.createDataFrame(
            [],
            schema=schema,
        )

        # Act
        profile: DataProfile = provider.compute_profile(
            dataframe=empty_dataframe,
            columns=None,
            config=default_config,
        )

        # Assert
        assert profile.row_count == 0
        assert len(profile.columns) == 2
        assert len(profile.column_profiles) == 0

    # ------------------------------------------------------------------
    # test_fingerprint_changes_with_schema
    # ------------------------------------------------------------------

    def test_fingerprint_changes_with_schema(
        self,
        provider: SparkDataProvider,
        spark_session: SparkSession,
        default_config: SimpleNamespace,
    ) -> None:
        """Verifica que schemas diferentes produzem fingerprints diferentes."""
        # Arrange
        schema_a: StructType = StructType(
            [StructField("nome", StringType(), nullable=True)],
        )
        schema_b: StructType = StructType(
            [StructField("idade", IntegerType(), nullable=True)],
        )
        dataframe_a: DataFrame = spark_session.createDataFrame(
            [("Alice",)],
            schema=schema_a,
        )
        dataframe_b: DataFrame = spark_session.createDataFrame(
            [(30,)],
            schema=schema_b,
        )

        # Act
        fingerprint_a: str = provider.compute_fingerprint(
            dataframe=dataframe_a,
            config=default_config,
        )
        fingerprint_b: str = provider.compute_fingerprint(
            dataframe=dataframe_b,
            config=default_config,
        )

        # Assert
        assert fingerprint_a != fingerprint_b
        assert isinstance(fingerprint_a, str)
        assert len(fingerprint_a) == 64  # SHA-256 hex
