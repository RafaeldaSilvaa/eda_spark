from __future__ import annotations

"""Fixtures compartilhadas para testes de integração com PySpark.

Todas as fixtures de sessão Spark e DataFrames de exemplo usadas
pelos testes de integração são definidas aqui.
"""

from datetime import date

import pytest
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


@pytest.fixture(scope="session")
def spark_session() -> SparkSession:
    """Fixture que fornece uma SparkSession em modo local para testes.

    Cria uma sessão com ``master("local[1]")`` e uma única partição
    de shuffle para garantir execução determinística em ambiente
    de teste.

    Yields:
        Sessão Spark configurada para testes de integração.
    """
    spark: SparkSession = (
        SparkSession.builder.master("local[1]")
        .appName("test")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.fixture
def sample_dataframe(
    spark_session: SparkSession,
) -> DataFrame:
    """Fixture que retorna um DataFrame com tipos mistos e valores nulos.

    Schema:
        - id: inteiro (chave primária)
        - nome: string (10% nulo)
        - valor: double (aproximadamente 14% nulo)
        - data_cadastro: date (aproximadamente 33% nulo)
        - ativo: boolean (não nulo)

    Returns:
        DataFrame com 100 linhas e 5 colunas.
    """
    schema: StructType = StructType(
        [
            StructField("id", IntegerType(), nullable=False),
            StructField("nome", StringType(), nullable=True),
            StructField("valor", DoubleType(), nullable=True),
            StructField("data_cadastro", DateType(), nullable=True),
            StructField("ativo", BooleanType(), nullable=False),
        ],
    )

    data: list[tuple[int, str | None, float | None, date | None, bool]] = []
    for i in range(100):
        nome: str | None = f"item_{i:04d}" if i % 10 != 0 else None
        valor: float | None = float(i * 1.5) if i % 7 != 0 else None
        data_cad: date | None = (
            date(2024, 1, 1) if i % 5 == 0 else (date(2024, 1, (i % 28) + 1) if i % 3 != 0 else None)
        )
        data.append((i, nome, valor, data_cad, i % 2 == 0))

    return spark_session.createDataFrame(data, schema=schema)


@pytest.fixture
def clean_dataframe(
    spark_session: SparkSession,
) -> DataFrame:
    """Fixture que retorna um DataFrame sem nulos, sem duplicatas.

    Schema:
        - id: inteiro
        - nome: string
        - altura: double
        - data_nascimento: date
        - ativo: boolean

    Returns:
        DataFrame com 50 linhas completamente preenchidas.
    """
    schema: StructType = StructType(
        [
            StructField("id", IntegerType(), nullable=False),
            StructField("nome", StringType(), nullable=False),
            StructField("altura", DoubleType(), nullable=False),
            StructField("data_nascimento", DateType(), nullable=False),
            StructField("ativo", BooleanType(), nullable=False),
        ],
    )

    data: list[tuple[int, str, float, date, bool]] = [
        (i, f"pessoa_{i:03d}", 1.50 + (i * 0.02), date(1990 + (i % 30), 1, (i % 28) + 1), i % 2 == 0) for i in range(50)
    ]

    return spark_session.createDataFrame(data, schema=schema)


@pytest.fixture
def null_dataframe(
    spark_session: SparkSession,
) -> DataFrame:
    """Fixture que retorna um DataFrame onde **todas** as células são nulas.

    Schema:
        - coluna_a: string (nullable)
        - coluna_b: double (nullable)
        - coluna_c: integer (nullable)

    Returns:
        DataFrame com 10 linhas totalmente nulas.
    """
    schema: StructType = StructType(
        [
            StructField("coluna_a", StringType(), nullable=True),
            StructField("coluna_b", DoubleType(), nullable=True),
            StructField("coluna_c", IntegerType(), nullable=True),
        ],
    )

    data: list[tuple[None, None, None]] = [(None, None, None) for _ in range(10)]

    return spark_session.createDataFrame(data, schema=schema)


@pytest.fixture
def constant_column_dataframe(
    spark_session: SparkSession,
) -> DataFrame:
    """Fixture que retorna um DataFrame com uma coluna de valor constante.

    Schema:
        - id: inteiro
        - constante: string (todos os valores são iguais)

    Returns:
        DataFrame com 20 linhas e uma coluna constante.
    """
    schema: StructType = StructType(
        [
            StructField("id", IntegerType(), nullable=False),
            StructField("constante", StringType(), nullable=False),
        ],
    )

    data: list[tuple[int, str]] = [(i, "mesmo_valor") for i in range(20)]

    return spark_session.createDataFrame(data, schema=schema)


@pytest.fixture
def duplicate_dataframe(
    spark_session: SparkSession,
) -> DataFrame:
    """Fixture que retorna um DataFrame com aproximadamente 20% de linhas duplicadas.

    Schema:
        - id: inteiro
        - valor: double
        - rotulo: string

    De 25 linhas totais, 5 são duplicatas exatas de outras 5,
    resultando em ~20% de duplicação.

    Returns:
        DataFrame com 25 linhas, sendo 5 duplicatas.
    """
    schema: StructType = StructType(
        [
            StructField("id", IntegerType(), nullable=False),
            StructField("valor", DoubleType(), nullable=False),
            StructField("rotulo", StringType(), nullable=False),
        ],
    )

    linhas_originais: list[tuple[int, float, str]] = [(i, float(i * 10), f"original_{i}") for i in range(20)]
    linhas_duplicadas: list[tuple[int, float, str]] = [(i, float(i * 10), f"original_{i}") for i in range(5)]

    data: list[tuple[int, float, str]] = linhas_originais + linhas_duplicadas

    return spark_session.createDataFrame(data, schema=schema)
