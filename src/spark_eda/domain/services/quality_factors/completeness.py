"""Fatores de qualidade para a dimensão **Completude**.

Avalia a presença de valores ausentes, nulos, vazios ou de
comprimento zero em todas as colunas do dataset.
"""

from __future__ import annotations

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.entities.statistic import TextStats
from spark_eda.domain.services.quality_factors import registrar
from spark_eda.domain.value_objects.severity import Severity


def _severity(score: float) -> Severity:
    """Mapeia uma pontuação em [0, 1] para um nível de severidade."""
    if score < 0.3:
        return Severity.CRITICAL
    if score < 0.6:
        return Severity.HIGH
    if score < 0.8:
        return Severity.MEDIUM
    return Severity.LOW


def _non_null_ratio(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de proporção de valores não nulos.

    Média de ``non_null_count / total`` em todas as colunas.
    Uma coluna sem valores nulos contribui com 1.0.
    """
    total_rows: int = profile.row_count
    if total_rows == 0:
        return QualityFactor(
            name="Proporção de valores não nulos",
            score=1.0,
            internal_weight=0.35,
            contribution=0.35,
            reason="Dataset vazio — todos os valores são considerados não nulos por definição.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    proportions: list[float] = []
    affected_columns: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        total_column: int = column_metadata.null_count + column_metadata.non_null_count
        if total_column == 0:
            proportion: float = 1.0
        else:
            proportion = column_metadata.non_null_count / total_column

        proportions.append(proportion)
        if proportion < 0.95:
            affected_columns.append(column_metadata.name)

    mean_value: float = sum(proportions) / len(proportions) if proportions else 1.0

    return QualityFactor(
        name="Proporção de valores não nulos",
        score=mean_value,
        internal_weight=0.35,
        contribution=mean_value * 0.35,
        reason=f"Média de {mean_value:.1%} de valores preenchidos entre {len(proportions)} colunas.",
        severity=_severity(mean_value),
        affected_columns=affected_columns,
    )


def _row_completeness(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de completude de linhas.

    Estima a proporção de linhas completamente preenchidas com base na
    fração de colunas que possuem valores nulos.
    """
    if len(profile.columns) == 0:
        return QualityFactor(
            name="Completude de linhas",
            score=1.0,
            internal_weight=0.30,
            contribution=0.30,
            reason="Nenhuma coluna para avaliar — considerando completude total.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    columns_with_nulls: int = sum(
        1 for cm in profile.columns if cm.null_count > 0
    )
    fraction_columns_with_nulls: float = columns_with_nulls / len(profile.columns)
    score: float = 1.0 - fraction_columns_with_nulls

    affected_columns: list[str] = [
        cm.name for cm in profile.columns if cm.null_count > 0
    ]

    return QualityFactor(
        name="Completude de linhas",
        score=score,
        internal_weight=0.30,
        contribution=score * 0.30,
        reason=(
            f"{columns_with_nulls} de {len(profile.columns)} colunas "
            f"possuem valores nulos. Score baseado na fração de colunas "
            f"completamente preenchidas."
        ),
        severity=_severity(score),
        affected_columns=affected_columns,
    )


def _empty_strings(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de proporção de strings vazias.

    Para colunas string que possuem :class:`TextStats`, utiliza o
    campo ``empty_ratio``. Demais colunas são ignoradas.
    """
    empty_ratios: list[float] = []
    affected_columns: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, TextStats):
            empty_ratios.append(stats.empty_ratio)
            if stats.empty_ratio > 0.05:
                affected_columns.append(column_metadata.name)

    if not empty_ratios:
        return QualityFactor(
            name="Proporção de strings vazias",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma coluna textual encontrada para avaliação.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    mean_empty: float = sum(empty_ratios) / len(empty_ratios)
    score: float = 1.0 - mean_empty

    return QualityFactor(
        name="Proporção de strings vazias",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(
            f"Média de {mean_empty:.1%} de valores vazios em "
            f"{len(empty_ratios)} colunas textuais."
        ),
        severity=_severity(score),
        affected_columns=affected_columns,
    )


def _zero_length_fields(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de campos de comprimento zero.

    Para colunas textuais com :class:`TextStats`, verifica se
    ``min_length == 0``, indicando a presença de strings vazias.
    """
    affected_columns: list[str] = []
    total_text: int = 0

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, TextStats):
            total_text += 1
            if stats.min_length == 0:
                affected_columns.append(column_metadata.name)

    if total_text == 0:
        return QualityFactor(
            name="Campos de comprimento zero",
            score=1.0,
            internal_weight=0.15,
            contribution=0.15,
            reason="Nenhuma coluna textual encontrada para avaliação.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    zero_proportion: float = len(affected_columns) / total_text
    score: float = 1.0 - zero_proportion

    return QualityFactor(
        name="Campos de comprimento zero",
        score=score,
        internal_weight=0.15,
        contribution=score * 0.15,
        reason=(
            f"{len(affected_columns)} de {total_text} colunas textuais "
            f"possuem pelo menos um registro com comprimento zero."
        ),
        severity=_severity(score),
        affected_columns=affected_columns,
    )


@registrar("completeness")
def calcular_score(profile: DataProfile) -> list[QualityFactor]:
    """Calcula todos os fatores para a dimensão **Completude**.

    Args:
        profile: Perfil completo do dataset com metadados,
            estatísticas e distribuições para cada coluna.

    Returns:
        Lista de quatro fatores de completude: proporção de não nulos,
        completude de linhas, strings vazias e campos de comprimento zero.
    """
    return [
        _non_null_ratio(profile),
        _row_completeness(profile),
        _empty_strings(profile),
        _zero_length_fields(profile),
    ]
