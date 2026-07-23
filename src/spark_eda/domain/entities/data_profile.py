"""Perfil completo do dataset."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile


@dataclass(frozen=True)
class DataProfile:
    """Perfil completo do dataset, incluindo estrutura e perfis individuais das colunas.

    Attributes:
        id: Identificador único do perfil (pode ser o nome do arquivo ou hash do dataset).
        columns: Tupla com metadados de todas as colunas na ordem original do schema.
        row_count: Número total de linhas (registros) no dataset.
        column_profiles: Dicionário mapeando nome da coluna ao seu ColumnProfile completo.
    """

    id: str
    columns: tuple[ColumnMetadata, ...]
    row_count: int
    column_profiles: dict[str, ColumnProfile]
