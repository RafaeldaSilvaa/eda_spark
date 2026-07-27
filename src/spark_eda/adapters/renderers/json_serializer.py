"""Serializador JSON para relatórios spark_eda."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


def _default_serializer(obj: Any) -> Any:
    """Serializador padrão para tipos não suportados nativamente por JSON.

    Args:
        obj: Objeto a ser serializado.

    Returns:
        Representação serializável do objeto.

    Raises:
        TypeError: Se o tipo não puder ser serializado.
    """
    if is_dataclass(obj):
        return asdict(obj)  # type: ignore[arg-type]
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Non-serializable type: {type(obj).__name__}")


class JSONSerializer:
    """Serializador de relatórios para o formato JSON.

    Converte DTOs do spark_eda em strings JSON para exportação,
    armazenamento ou integração com outras ferramentas.
    """

    @staticmethod
    def serialize_report(report: object) -> str:
        """Serializa um relatório completo para JSON.

        Args:
            report: Objeto de relatório (``EDAReport``, ``QualityReport``,
                ou qualquer dataclass).

        Returns:
            String JSON formatada com indentação.
        """
        return json.dumps(
            asdict(report) if is_dataclass(report) else report,  # type: ignore[arg-type]
            default=_default_serializer,
            indent=2,
            ensure_ascii=False,
        )

    @staticmethod
    def serialize_quality(quality_report: object) -> str:
        """Serializa um relatório de qualidade para JSON.

        Args:
            quality_report: Objeto ``QualityReport``.

        Returns:
            String JSON formatada com indentação.
        """
        return JSONSerializer.serialize_report(quality_report)
