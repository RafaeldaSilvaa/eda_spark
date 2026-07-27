"""Fatores de qualidade para a dimensão **Acurácia**.

Avalia a precisão dos dados: presença de outliers, conformidade de
formato, dados suspeitos, dados corrompidos e violações de regras
de negócio.
"""

from __future__ import annotations

from datetime import date
from statistics import mean

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.entities.statistic import NumericStats, TextStats
from spark_eda.domain.services.quality_factors import _score_severity, registrar
from spark_eda.domain.value_objects.severity import Severity

_OUTLIER_WARN_THRESHOLD = 0.05
_NULL_INCONSISTENCY_THRESHOLD = 0.2
_YEAR_MIN_PLAUSIBLE = 1900.0
_MONTH_MAX = 12.0
_DAY_MAX = 31.0
_PERCENTAGE_MAX = 100.0
_AGE_MAX_PLAUSIBLE = 120.0


def _outlier_ratio(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de proporção de outliers.

    Utiliza :class:`OutlierInfo` das colunas numéricas para determinar
    a taxa média de outliers. Quanto menor a taxa, maior a pontuação.
    """
    outlier_ratios: list[float] = []
    columns_with_outliers: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        outlier_info = column_profile.outlier
        if outlier_info is not None:
            outlier_ratios.append(outlier_info.ratio)
            if outlier_info.ratio > _OUTLIER_WARN_THRESHOLD:
                columns_with_outliers.append(column_metadata.name)

    if not outlier_ratios:
        return QualityFactor(
            name="Proporção de outliers",
            score=1.0,
            internal_weight=0.25,
            contribution=0.25,
            reason="Nenhuma informação de outlier disponível — fator considerado neutro.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    mean_outlier: float = mean(outlier_ratios)
    score: float = 1.0 - mean_outlier

    return QualityFactor(
        name="Proporção de outliers",
        score=score,
        internal_weight=0.25,
        contribution=score * 0.25,
        reason=(
            f"Taxa média de outliers de {mean_outlier:.2%} entre "
            f"{len(outlier_ratios)} colunas com detecção de outliers."
        ),
        severity=_score_severity(score),
        affected_columns=columns_with_outliers,
    )


def _format_accuracy(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de acurácia de formato.

    Verifica colunas com tipos inferidos (CPF, CNPJ, email, etc.)
    usando a proporção de não nulos como proxy para conformidade de formato.
    """
    columns_with_inferred_type: int = 0
    inconsistent_columns: list[str] = []

    for column_metadata in profile.columns:
        if column_metadata.inferred_type is not None:
            columns_with_inferred_type += 1
            total_column: int = column_metadata.null_count + column_metadata.non_null_count
            if total_column > 0:
                null_ratio: float = column_metadata.null_count / total_column
                if null_ratio > _NULL_INCONSISTENCY_THRESHOLD:
                    inconsistent_columns.append(column_metadata.name)

    if columns_with_inferred_type == 0:
        return QualityFactor(
            name="Acurácia de formato",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma coluna com tipo semântico inferido disponível.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(inconsistent_columns) / columns_with_inferred_type)

    return QualityFactor(
        name="Acurácia de formato",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(
            f"{len(inconsistent_columns)} de {columns_with_inferred_type} "
            f"colunas com tipo inferido possuem alta taxa de nulos, "
            f"possível indicativo de dados em formato incorreto."
        ),
        severity=_score_severity(score),
        affected_columns=inconsistent_columns,
    )


def _suspicious_data(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de dados suspeitos.

    Identifica valores extremos que podem ser suspeitos usando o
    intervalo interquartil (IQR) de colunas numéricas. Outliers além
    de 3x IQR são marcados como suspeitos.
    """
    suspicious_columns: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        outlier_info = column_profile.outlier

        if isinstance(stats, NumericStats) and outlier_info is not None:
            iqr: float = stats.q75 - stats.q25
            upper_extreme_limit: float = stats.q75 + 3.0 * iqr
            lower_extreme_limit: float = stats.q25 - 3.0 * iqr

            if outlier_info.bounds_upper is not None and stats.max > upper_extreme_limit:
                suspicious_columns.append(column_metadata.name)
            if outlier_info.bounds_lower is not None and stats.min < lower_extreme_limit and column_metadata.name not in suspicious_columns:  # noqa: E501
                suspicious_columns.append(column_metadata.name)

    if not suspicious_columns:
        return QualityFactor(
            name="Dados suspeitos",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhum valor extremo suspeito identificado nas colunas analisadas.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(suspicious_columns) / len(profile.columns))

    return QualityFactor(
        name="Dados suspeitos",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(
            f"{len(suspicious_columns)} coluna(s) numérica(s) possuem "
            f"valores extremos suspeitos (alem de 3x IQR)."
        ),
        severity=_score_severity(score),
        affected_columns=list(suspicious_columns),
    )


def _corrupted_data(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de dados corrompidos.

    Verifica valores impossíveis ou inconsistentes:
    comprimento mínimo negativo em colunas TextStats.
    """
    corrupted_columns: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats

        if isinstance(stats, TextStats) and stats.min_length < 0:
            corrupted_columns.append(column_metadata.name)

    if not corrupted_columns:
        return QualityFactor(
            name="Dados corrompidos",
            score=1.0,
            internal_weight=0.15,
            contribution=0.15,
            reason="Nenhum indício de dados corrompidos identificado.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = 1.0 - (len(corrupted_columns) / max(len(profile.columns), 1))

    return QualityFactor(
        name="Dados corrompidos",
        score=score,
        internal_weight=0.15,
        contribution=score * 0.15,
        reason=(
            f"{len(corrupted_columns)} colunas apresentam valores "
            f"impossíveis (ex.: comprimento mínimo negativo)."
        ),
        severity=_score_severity(score),
        affected_columns=corrupted_columns,
    )


def _business_rules(profile: DataProfile) -> QualityFactor:  # noqa: PLR0912
    """Calcula o fator de violação de regras de negócio.

    Aplica regras de negócio comuns:
    * Colunas de ano (nome contendo ``ano``) devem ter valores entre 1900 e ano atual + 5.
    * Colunas de mês (``mes``, ``month``) devem ter valores entre 1 e 12.
    * Colunas de dia (``dia``, ``day``) devem ter valores entre 1 e 31.
    * Colunas de percentual (``pct``, ``perc``, ``percentual``) devem ter valores entre 0 e 100.
    * Colunas de idade (``idade``, ``age``) devem ter valores entre 0 e 120.
    """
    violated_columns: set[str] = set()
    violation_details: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if not isinstance(stats, NumericStats):
            continue

        normalized_name: str = column_metadata.name.lower().replace("_", "").replace("-", "")

        if "ano" in normalized_name:
            year_upper: int = date.today().year + 5
            if stats.min < _YEAR_MIN_PLAUSIBLE or stats.max > year_upper:
                violated_columns.add(column_metadata.name)
                violation_details.append(
                    f"{column_metadata.name}: ano fora do intervalo [1900, {year_upper}] "
                    f"(min={stats.min:.0f}, max={stats.max:.0f})"
                )

        if (normalized_name in ("mes", "month") or normalized_name.startswith("mes") or normalized_name.startswith("month")) and (stats.min < 1.0 or stats.max > _MONTH_MAX):  # noqa: E501
            violated_columns.add(column_metadata.name)
            violation_details.append(
                f"{column_metadata.name}: mês fora do intervalo [1, {_MONTH_MAX:.0f}]"
            )

        if (normalized_name in ("dia", "day") or normalized_name.startswith("dia") or normalized_name.startswith("day")) and (stats.min < 1.0 or stats.max > _DAY_MAX):  # noqa: E501
            violated_columns.add(column_metadata.name)
            violation_details.append(
                f"{column_metadata.name}: dia fora do intervalo [1, {_DAY_MAX:.0f}]"
            )

        percentage_patterns: tuple[str, ...] = ("pct", "perc", "percentual", "porcentagem")
        for pattern in percentage_patterns:
            if pattern in normalized_name:
                if stats.min < 0.0 or stats.max > _PERCENTAGE_MAX:
                    violated_columns.add(column_metadata.name)
                    violation_details.append(
                        f"{column_metadata.name}: percentual fora de [0, {_PERCENTAGE_MAX:.0f}]"
                    )
                break

        age_patterns: tuple[str, ...] = ("idade", "age", "idadeanos", "anos")
        for pattern in age_patterns:
            if pattern in normalized_name:
                if stats.min < 0.0 or stats.max > _AGE_MAX_PLAUSIBLE:
                    violated_columns.add(column_metadata.name)
                    violation_details.append(
                        f"{column_metadata.name}: idade fora do intervalo [0, {_AGE_MAX_PLAUSIBLE:.0f}]"
                    )
                break

    if not violated_columns:
        return QualityFactor(
            name="Regras de negócio",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma violação de regra de negócio identificada.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    violation_ratio: float = len(violated_columns) / max(len(profile.columns), 1)
    score: float = 1.0 - violation_ratio

    return QualityFactor(
        name="Regras de negócio",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=" | ".join(violation_details),
        severity=_score_severity(score),
        affected_columns=list(violated_columns),
    )


@registrar("accuracy")
def calcular_score(profile: DataProfile) -> list[QualityFactor]:
    """Calcula todos os fatores para a dimensão **Acurácia**.

    Args:
        profile: Perfil completo do dataset.

    Returns:
        Lista de cinco fatores de acurácia: proporção de outliers,
        acurácia de formato, dados suspeitos, dados corrompidos e
        regras de negócio.
    """
    return [
        _outlier_ratio(profile),
        _format_accuracy(profile),
        _suspicious_data(profile),
        _corrupted_data(profile),
        _business_rules(profile),
    ]
