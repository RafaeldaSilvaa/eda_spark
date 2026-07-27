"""Fatores de qualidade para a dimensão **Atualidade**.

Avalia a atualidade dos dados, completude temporal, datas inválidas
e lacunas temporais em séries.
"""

from __future__ import annotations

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.entities.statistic import TemporalStats
from spark_eda.domain.services.quality_factors import _score_severity, registrar
from spark_eda.domain.value_objects.severity import Severity

_TIMELINESS_THRESHOLD = 0.95
_STALE_THRESHOLD = 0.05


def _freshness(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de atualidade dos dados.

    Utiliza colunas temporais disponíveis para avaliar a atualidade do dataset.
    Colunas com dados mais recentes são consideradas mais atualizadas.
    A pontuação é baseada na presença e não obsolescência das datas.
    """
    temporal_columns: list[str] = []
    columns_with_recent_data: int = 0

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, TemporalStats):
            temporal_columns.append(column_metadata.name)
            if stats.range_days > 0:
                columns_with_recent_data += 1

    if not temporal_columns:
        return QualityFactor(
            name="Atualidade dos dados",
            score=1.0,
            internal_weight=0.30,
            contribution=0.30,
            reason="Nenhuma coluna temporal encontrada — fator considerado neutro.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = columns_with_recent_data / len(temporal_columns)

    return QualityFactor(
        name="Atualidade dos dados",
        score=score,
        internal_weight=0.30,
        contribution=score * 0.30,
        reason=(
            f"{columns_with_recent_data} de {len(temporal_columns)} "
            f"colunas temporais possuem dados com variação positiva "
            f"(range_days > 0), indicando atualidade."
        ),
        severity=_score_severity(score),
        affected_columns=temporal_columns,
    )


def _temporal_completeness(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de completude temporal.

    Avalia a proporção de não nulos em colunas temporais
    (date, timestamp) como proxy para a completude da dimensão temporal.
    """
    non_null_proportions: list[float] = []
    affected_columns: list[str] = []

    for column_metadata in profile.columns:
        if column_metadata.data_type.value in ("date", "timestamp"):
            total_column: int = column_metadata.null_count + column_metadata.non_null_count
            if total_column == 0:
                proportion: float = 1.0
            else:
                proportion = column_metadata.non_null_count / total_column

            non_null_proportions.append(proportion)
            if proportion < _TIMELINESS_THRESHOLD:
                affected_columns.append(column_metadata.name)

    if not non_null_proportions:
        return QualityFactor(
            name="Completude temporal",
            score=1.0,
            internal_weight=0.25,
            contribution=0.25,
            reason="Nenhuma coluna temporal encontrada — fator considerado neutro.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    mean_value: float = sum(non_null_proportions) / len(non_null_proportions)
    score: float = mean_value

    return QualityFactor(
        name="Completude temporal",
        score=score,
        internal_weight=0.25,
        contribution=score * 0.25,
        reason=(f"Média de {mean_value:.1%} de valores preenchidos em {len(non_null_proportions)} colunas temporais."),
        severity=_score_severity(score),
        affected_columns=affected_columns,
    )


def _invalid_dates(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de datas inválidas.

    Utiliza a contagem de nulos em colunas temporais como proxy para
    datas inválidas (valores que não puderam ser interpretados como datas
    resultam em nulo).
    """
    null_ratios: list[float] = []
    affected_columns: list[str] = []

    for column_metadata in profile.columns:
        if column_metadata.data_type.value in ("date", "timestamp"):
            total_column: int = column_metadata.null_count + column_metadata.non_null_count
            if total_column == 0:
                null_ratio_val: float = 0.0
            else:
                null_ratio_val = column_metadata.null_count / total_column

            null_ratios.append(null_ratio_val)
            if null_ratio_val > _STALE_THRESHOLD:
                affected_columns.append(column_metadata.name)

    if not null_ratios:
        return QualityFactor(
            name="Datas inválidas",
            score=1.0,
            internal_weight=0.25,
            contribution=0.25,
            reason="Nenhuma coluna temporal encontrada — fator considerado neutro.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    mean_nulls: float = sum(null_ratios) / len(null_ratios)
    score: float = 1.0 - mean_nulls

    return QualityFactor(
        name="Datas inválidas",
        score=score,
        internal_weight=0.25,
        contribution=score * 0.25,
        reason=(
            f"Média de {mean_nulls:.1%} de valores nulos em colunas "
            f"temporais, possivelmente indicando datas inválidas ou "
            f"mal formatadas."
        ),
        severity=_score_severity(score),
        affected_columns=affected_columns,
    )


def _temporal_gaps(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de lacunas temporais.

    Utiliza o campo ``gap_count`` de :class:`TemporalStats` para
    identificar séries temporais descontínuas. Cada lacuna reduz a
    pontuação proporcionalmente.
    """
    total_gaps: int = 0
    columns_with_gap: list[str] = []
    temporal_columns_with_stats: int = 0

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, TemporalStats):
            temporal_columns_with_stats += 1
            if stats.gap_count > 0:
                total_gaps += stats.gap_count
                columns_with_gap.append(column_metadata.name)

    if temporal_columns_with_stats == 0:
        return QualityFactor(
            name="Lacunas temporais",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma coluna temporal com estatísticas disponíveis.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 / (1.0 + total_gaps)

    return QualityFactor(
        name="Lacunas temporais",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(f"Total de {total_gaps} lacunas temporais identificadas em {len(columns_with_gap)} colunas."),
        severity=_score_severity(score),
        affected_columns=columns_with_gap,
    )


@registrar("timeliness")
def calcular_score(profile: DataProfile) -> list[QualityFactor]:
    """Calcula todos os fatores para a dimensão **Atualidade**.

    Args:
        profile: Perfil completo do dataset.

    Returns:
        Lista de quatro fatores de atualidade: atualidade dos dados,
        completude temporal, datas inválidas e lacunas temporais.
    """
    return [
        _freshness(profile),
        _temporal_completeness(profile),
        _invalid_dates(profile),
        _temporal_gaps(profile),
    ]
