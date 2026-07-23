"""Metadados descritivos de uma coluna do dataset."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.inferred_type import InferredType


@dataclass(frozen=True)
class ColumnMetadata:
    """Metadados descritivos de uma coluna do dataset.

    Attributes:
        name: Nome da coluna conforme definido no schema original.
        data_type: Tipo de dado primitivo da coluna.
        nullable: Indica se a coluna aceita valores nulos.
        inferred_type: Tipo semântico inferido a partir dos valores, se aplicável.
        null_count: Quantidade de valores nulos presentes na coluna.
        non_null_count: Quantidade de valores não nulos presentes na coluna.
    """

    name: str
    data_type: DataType
    nullable: bool
    inferred_type: InferredType | None
    null_count: int
    non_null_count: int
