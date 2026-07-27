"""Perfil completo de uma coluna do dataset."""

from __future__ import annotations

from dataclasses import dataclass

from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.distribution import Distribution
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.domain.entities.statistic import Statistic


@dataclass(frozen=True)
class ColumnProfile:
    """Perfil completo de uma coluna, reunindo metadados, estatísticas, distribuição e outliers.

    Attributes:
        metadata: Metadados descritivos da coluna (nome, tipo, nulabilidade etc.).
        stats: Estatísticas descritivas computadas conforme o tipo da coluna,
               ou None se não for possível calcular.
        distribution: Distribuição de valores da coluna, ou None se indisponível.
        outlier: Informações sobre outliers detectados, ou None se não analisado.
    """

    metadata: ColumnMetadata
    stats: Statistic | None
    distribution: Distribution | None
    outlier: OutlierInfo | None
