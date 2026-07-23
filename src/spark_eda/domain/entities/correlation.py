"""Correlação calculada entre duas colunas do dataset."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.value_objects.correlation_method import CorrelationMethod


@dataclass(frozen=True)
class Correlation:
    """Correlação calculada entre duas colunas do dataset.

    Attributes:
        column_a: Nome da primeira coluna envolvida na correlação.
        column_b: Nome da segunda coluna envolvida na correlação.
        method: Método estatístico utilizado para o cálculo.
        value: Valor numérico da correlação, variando conforme o método.
    """

    column_a: str
    column_b: str
    method: CorrelationMethod
    value: float
