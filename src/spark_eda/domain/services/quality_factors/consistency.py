"""Fatores de qualidade para a dimensão **Consistência**.

Avalia a coerência interna dos dados: tipos, intervalos, integridade
do esquema, consistência entre colunas e conformidade de formato.
"""

from __future__ import annotations

from statistics import mean

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.entities.statistic import (
    BooleanStats,
    CategoricalStats,
    NumericStats,
    TemporalStats,
    TextStats,
)
from spark_eda.domain.services.quality_factors import _score_severity, registrar
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.severity import Severity

_FK_NULL_THRESHOLD = 0.1


def _type_consistency(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de consistência de tipos.

    Verifica se o tipo declarado da coluna é compatível com as
    estatísticas disponíveis. Por exemplo, colunas numéricas devem ter
    :class:`NumericStats`, colunas de texto devem ter
    :class:`TextStats` ou :class:`CategoricalStats`.
    """
    inconsistent_columns: list[str] = []
    valid_columns: int = 0

    expected_type_mapping: dict[DataType, type | tuple[type, ...]] = {
        DataType.INTEGER: NumericStats,
        DataType.LONG: NumericStats,
        DataType.DOUBLE: NumericStats,
        DataType.DECIMAL: NumericStats,
        DataType.STRING: (CategoricalStats, TextStats),
        DataType.DATE: TemporalStats,
        DataType.TIMESTAMP: TemporalStats,
        DataType.BOOLEAN: BooleanStats,
    }

    for column_metadata in profile.columns:
        expected_type = expected_type_mapping.get(column_metadata.data_type)
        if expected_type is None:
            continue

        valid_columns += 1
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats

        if stats is None or not isinstance(stats, expected_type):
            inconsistent_columns.append(column_metadata.name)

    if valid_columns == 0:
        return QualityFactor(
            name="Consistência de tipos",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma coluna com tipo mapeável para verificação de consistência.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(inconsistent_columns) / valid_columns)

    return QualityFactor(
        name="Consistência de tipos",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(
            f"{len(inconsistent_columns)} de {valid_columns} colunas "
            f"apresentam incompatibilidade entre tipo declarado e "
            f"estatísticas observadas."
        ),
        severity=_score_severity(score),
        affected_columns=inconsistent_columns,
    )


def _range_consistency(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de consistência de intervalos.

    Para colunas numéricas, verifica se valores como ``min`` e ``max``
    são coerentes (ex.: sem valores negativos em colunas de quantidade
    absoluta como ``qtd_*``, ``count_*``).
    """
    inconsistent_columns: list[str] = []
    total_numeric: int = 0

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if not isinstance(stats, NumericStats):
            continue

        total_numeric += 1
        normalized_name: str = column_metadata.name.lower().replace("_", "").replace("-", "")

        is_absolute_quantity: bool = any(
            pattern in normalized_name for pattern in ("qtd", "count", "qtde", "quantidade", "numero", "nr", "num")
        )

        if is_absolute_quantity and stats.min < 0.0:
            inconsistent_columns.append(column_metadata.name)

        if stats.min > stats.max:
            inconsistent_columns.append(column_metadata.name)

    if total_numeric == 0:
        return QualityFactor(
            name="Consistência de intervalos",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma coluna numérica disponível para verificação de intervalos.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(inconsistent_columns) / total_numeric)

    return QualityFactor(
        name="Consistência de intervalos",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(
            f"{len(inconsistent_columns)} de {total_numeric} colunas "
            f"numéricas apresentam valores fora do intervalo esperado "
            f"(ex.: valores negativos em campos de quantidade)."
        ),
        severity=_score_severity(score),
        affected_columns=inconsistent_columns,
    )


def _cross_column_consistency(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de consistência entre colunas.

    Verifica pares de colunas cujos nomes sugerem um relacionamento (ex.:
    ``data_inicio`` / ``data_fim``, ``valor_total`` / ``valor_parcela``)
    com base na coerência de suas estatísticas.
    """
    inconsistent_columns: set[str] = set()

    temporal_pairs: list[tuple[str, str]] = []
    column_names: set[str] = {cm.name for cm in profile.columns}

    for column_metadata in profile.columns:
        normalized_name: str = column_metadata.name.lower()
        if normalized_name.endswith("_fim") or normalized_name.endswith("_final"):
            base: str = normalized_name.rsplit("_", 1)[0]
            start_variant: str = f"{base}_inicio"
            ini_variant: str = f"{base}_ini"
            for candidate in column_names:
                cn_lower: str = candidate.lower()
                if cn_lower in (start_variant, ini_variant):
                    temporal_pairs.append((column_metadata.name, candidate))

    for end_column, start_column in temporal_pairs:
        end_profile: ColumnProfile = profile.column_profiles[end_column]
        start_profile: ColumnProfile = profile.column_profiles[start_column]

        end_stats = end_profile.stats
        start_stats = start_profile.stats

        if (
            isinstance(end_stats, TemporalStats)
            and isinstance(start_stats, TemporalStats)
            and start_stats.min_date > end_stats.min_date
        ):
            inconsistent_columns.add(start_column)
            inconsistent_columns.add(end_column)

    pair_count: int = len(temporal_pairs)

    if pair_count == 0:
        return QualityFactor(
            name="Consistência entre colunas",
            score=1.0,
            internal_weight=0.15,
            contribution=0.15,
            reason="Nenhum par de colunas relacionadas identificado para verificação.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(inconsistent_columns) / (pair_count * 2))

    return QualityFactor(
        name="Consistência entre colunas",
        score=score,
        internal_weight=0.15,
        contribution=score * 0.15,
        reason=(
            f"{len(inconsistent_columns)} colunas envolvidas em "
            f"{pair_count} pares relacionados apresentam inconsistências "
            f"(ex.: data de fim anterior à data de início)."
        ),
        severity=_score_severity(score),
        affected_columns=sorted(inconsistent_columns),
    )


def _schema_integrity(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de integridade do esquema.

    Verifica se colunas marcadas como ``nullable = False`` realmente
    possuem ``null_count == 0`` e se a contagem total de colunas é coerente.
    """
    violated_columns: list[str] = []

    for column_metadata in profile.columns:
        if not column_metadata.nullable and column_metadata.null_count > 0:
            violated_columns.append(column_metadata.name)

    if len(profile.columns) == 0:
        return QualityFactor(
            name="Integridade do esquema",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Dataset sem colunas definidas.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(violated_columns) / len(profile.columns))

    return QualityFactor(
        name="Integridade do esquema",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(
            f"{len(violated_columns)} colunas violam a restrição de "
            f"nulabilidade (nullable=False mas possuem valores nulos)."
        ),
        severity=_score_severity(score),
        affected_columns=violated_columns,
    )


def _referential_integrity(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de integridade referencial.

    Sem definições explícitas de chaves estrangeiras, usa uma heurística
    baseada em nomes sugestivos de colunas (ex.: ``*_id``) para verificar
    se todos os valores são não nulos e aparentam ser válidos.
    """
    sensitive_columns: list[str] = []

    for column_metadata in profile.columns:
        normalized_name: str = column_metadata.name.lower()
        if normalized_name.endswith("_id") or normalized_name.endswith("_fk"):
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            stats = column_profile.stats
            if isinstance(stats, CategoricalStats) and column_metadata.null_count > 0:
                sensitive_columns.append(column_metadata.name)

    if len(sensitive_columns) == 0:
        return QualityFactor(
            name="Integridade referencial",
            score=1.0,
            internal_weight=0.10,
            contribution=0.10,
            reason="Nenhuma coluna com indícios de chave estrangeira encontrada.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    null_ratios: list[float] = []
    for col_name in sensitive_columns:
        col_profile: ColumnProfile | None = profile.column_profiles.get(col_name)
        if col_profile is not None:
            meta = col_profile.metadata
            total: int = meta.non_null_count + meta.null_count
            if total > 0:
                null_ratios.append(meta.null_count / total)

    score: float
    reason: str
    avg_null_ratio: float = mean(null_ratios) if null_ratios else 0.0
    score = max(0.0, 1.0 - avg_null_ratio)
    reason = (
        (f"Média de {avg_null_ratio:.1%} de nulos em {len(null_ratios)} coluna(s) com indícios de chave estrangeira.")
        if null_ratios
        else ("Colunas FK encontradas, porém sem nulos — sem evidências de violação de integridade referencial.")
    )

    return QualityFactor(
        name="Integridade referencial",
        score=score,
        internal_weight=0.10,
        contribution=score * 0.10,
        reason=reason,
        severity=_score_severity(score),
        affected_columns=sensitive_columns,
    )


def _format_consistency(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de consistência de formato.

    Para colunas com :class:`InferredType` definido (CPF, CNPJ, email,
    etc.), verifica a proporção de nulos como proxy indireto para
    conformidade de formato.
    """
    columns_with_inferred_type: int = 0
    inconsistent_columns: list[str] = []

    for column_metadata in profile.columns:
        if column_metadata.inferred_type is not None:
            columns_with_inferred_type += 1
            total_column: int = column_metadata.null_count + column_metadata.non_null_count
            if total_column > 0:
                null_ratio: float = column_metadata.null_count / total_column
                if null_ratio > _FK_NULL_THRESHOLD:
                    inconsistent_columns.append(column_metadata.name)

    if columns_with_inferred_type == 0:
        return QualityFactor(
            name="Consistência de formato",
            score=1.0,
            internal_weight=0.15,
            contribution=0.15,
            reason="Nenhuma coluna com tipo semântico inferido disponível.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(inconsistent_columns) / columns_with_inferred_type)

    return QualityFactor(
        name="Consistência de formato",
        score=score,
        internal_weight=0.15,
        contribution=score * 0.15,
        reason=(
            f"{len(inconsistent_columns)} de {columns_with_inferred_type} "
            f"colunas com tipo inferido possuem alta taxa de nulos, "
            f"possível indicativo de dados em formato incorreto."
        ),
        severity=_score_severity(score),
        affected_columns=inconsistent_columns,
    )


@registrar("consistency")
def calcular_score(profile: DataProfile) -> list[QualityFactor]:
    """Calcula todos os fatores para a dimensão **Consistência**.

    Args:
        profile: Perfil completo do dataset.

    Returns:
        Lista de seis fatores de consistência: tipos, intervalos,
        consistência entre colunas, integridade do esquema, integridade
        referencial e consistência de formato.
    """
    return [
        _type_consistency(profile),
        _range_consistency(profile),
        _cross_column_consistency(profile),
        _schema_integrity(profile),
        _referential_integrity(profile),
        _format_consistency(profile),
    ]
