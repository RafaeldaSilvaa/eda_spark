from __future__ import annotations

"""Fábricas de dados para testes — cria entidades de domínio e DataFrames de exemplo."""

from datetime import date

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

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.value_objects.data_type import DataType


def create_sample_dataframe(
    spark: SparkSession,
    rows: int = 100,
) -> DataFrame:
    """Cria um DataFrame PySpark com tipos mistos para testes.

    O DataFrame gerado contém colunas dos tipos inteiro, string,
    double, date e boolean, com aproximadamente 10% de valores
    nulos distribuídos aleatoriamente.

    Args:
        spark: Sessão Spark ativa.
        rows: Número de linhas a gerar (padrão: 100).

    Returns:
        DataFrame com ``rows`` linhas e 5 colunas de tipos variados.
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
    for i in range(rows):
        nome: str | None = f"item_{i:04d}" if i % 10 != 0 else None
        valor: float | None = float(i * 1.5) if i % 7 != 0 else None
        data_cad: date | None = (
            date(2024, 1, 1) if i % 5 == 0 else (date(2024, 1, (i % 28) + 1) if i % 3 != 0 else None)
        )
        data.append((i, nome, valor, data_cad, i % 2 == 0))

    return spark.createDataFrame(data, schema=schema)


def create_column_metadata(
    name: str,
    type_: DataType,
    nullable: bool = True,
    nulls: int = 0,
    non_nulls: int = 100,
) -> ColumnMetadata:
    """Cria um :class:`ColumnMetadata` com valores padrão para testes.

    Args:
        name: Nome da coluna.
        type_: Tipo de dado da coluna.
        nullable: Indica se a coluna aceita nulos.
        nulls: Quantidade de valores nulos.
        non_nulls: Quantidade de valores não nulos.

    Returns:
        Instância de :class:`ColumnMetadata` configurada.
    """
    return ColumnMetadata(
        name=name,
        data_type=type_,
        nullable=nullable,
        inferred_type=None,
        null_count=nulls,
        non_null_count=non_nulls,
    )


def create_data_profile(
    id_: str,
    columns: list[ColumnMetadata],
    rows: int,
    col_profiles: dict[str, ColumnProfile] | None = None,
) -> DataProfile:
    """Cria um :class:`DataProfile` simplificado para testes.

    Args:
        id_: Identificador único do perfil.
        columns: Lista de metadados das colunas.
        rows: Número de linhas do dataset.
        col_profiles: Dicionário opcional de perfis de coluna.
            Se não fornecido, cria perfis vazios para cada coluna.

    Returns:
        Instância de :class:`DataProfile` configurada.
    """
    resolved_profiles: dict[str, ColumnProfile] = col_profiles if col_profiles is not None else {}

    if not resolved_profiles:
        for col in columns:
            resolved_profiles[col.name] = ColumnProfile(
                metadata=col,
                stats=None,
                distribution=None,
                outlier=None,
            )

    return DataProfile(
        id=id_,
        columns=tuple(columns),
        row_count=rows,
        column_profiles=resolved_profiles,
    )
