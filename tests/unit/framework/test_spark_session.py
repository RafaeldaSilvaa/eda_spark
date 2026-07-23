from __future__ import annotations

"""Testes para o gerenciamento de SparkSession.

Testa get_or_create_spark_session com mocks, sem dependência
de um cluster Spark real.
"""

from unittest import mock

from spark_eda.framework.spark_session import get_or_create_spark_session


def _make_builder_mock() -> mock.MagicMock:
    """Cria um MagicMock para SparkSession.Builder onde cada
    método da cadeia retorna o próprio builder.
    """
    builder: mock.MagicMock = mock.MagicMock()
    builder.appName.return_value = builder
    builder.config.return_value = builder
    return builder


class TestSparkSession:
    """Testes para o módulo spark_session."""

    def test_get_or_create_with_defaults(self) -> None:
        """get_or_create_spark_session com parâmetros padrão deve
        configurar AQE e não definir shuffle.partitions.
        """
        # Arrange
        builder: mock.MagicMock = _make_builder_mock()
        with mock.patch(
            "spark_eda.framework.spark_session.SparkSession.builder",
            builder,
        ):
            # Act
            result: object = get_or_create_spark_session()

        # Assert
        assert result is builder.getOrCreate.return_value
        builder.appName.assert_called_once_with("spark_eda")
        builder.config.assert_any_call("spark.sql.adaptive.enabled", "true")
        builder.config.assert_any_call(
            "spark.sql.adaptive.advisoryPartitionSizeInBytes", "64MB",
        )
        # shuffle.partitions NÃO deve ser configurado
        calls: list[tuple] = [
            c for c in builder.config.call_args_list
            if c[0][0] == "spark.sql.shuffle.partitions"
        ]
        assert len(calls) == 0

    def test_get_or_create_with_custom_app_name(self) -> None:
        """get_or_create_spark_session deve usar o app_name
        fornecido.
        """
        # Arrange
        builder: mock.MagicMock = _make_builder_mock()
        with mock.patch(
            "spark_eda.framework.spark_session.SparkSession.builder",
            builder,
        ):
            # Act
            get_or_create_spark_session(app_name="my_app")

        # Assert
        builder.appName.assert_called_once_with("my_app")

    def test_get_or_create_with_shuffle_partitions(self) -> None:
        """get_or_create_spark_session com shuffle_partitions deve
        configurar spark.sql.shuffle.partitions.
        """
        # Arrange
        builder: mock.MagicMock = _make_builder_mock()
        with mock.patch(
            "spark_eda.framework.spark_session.SparkSession.builder",
            builder,
        ):
            # Act
            get_or_create_spark_session(shuffle_partitions=200)

        # Assert
        builder.config.assert_any_call("spark.sql.shuffle.partitions", 200)

    def test_get_or_create_with_custom_partition_size(self) -> None:
        """get_or_create_spark_session deve usar o
        adapter_partition_size fornecido.
        """
        # Arrange
        builder: mock.MagicMock = _make_builder_mock()
        with mock.patch(
            "spark_eda.framework.spark_session.SparkSession.builder",
            builder,
        ):
            # Act
            get_or_create_spark_session(adapter_partition_size="128MB")

        # Assert
        builder.config.assert_any_call(
            "spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB",
        )

    def test_get_or_create_configures_adaptive_features(self) -> None:
        """get_or_create_spark_session deve habilitar AQE,
        coalescePartitions e skewJoin.
        """
        # Arrange
        builder: mock.MagicMock = _make_builder_mock()
        with mock.patch(
            "spark_eda.framework.spark_session.SparkSession.builder",
            builder,
        ):
            # Act
            get_or_create_spark_session()

        # Assert
        builder.config.assert_any_call("spark.sql.adaptive.enabled", "true")
        builder.config.assert_any_call(
            "spark.sql.adaptive.coalescePartitions.enabled", "true",
        )
        builder.config.assert_any_call(
            "spark.sql.adaptive.skewJoin.enabled", "true",
        )
