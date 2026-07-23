"""Tipos de dados suportados para colunas do dataset."""

from __future__ import annotations

from enum import Enum


class DataType(Enum):
    """Enumeração dos tipos de dados que uma coluna pode assumir."""

    INTEGER = "integer"
    LONG = "long"
    DOUBLE = "double"
    STRING = "string"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    DECIMAL = "decimal"
    BINARY = "binary"
    ARRAY = "array"
    STRUCT = "struct"
    MAP = "map"
    OTHER = "other"
