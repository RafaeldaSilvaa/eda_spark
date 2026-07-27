"""Fatores de qualidade para a dimensão **Unicidade**.

Avalia a presença de duplicatas, colunas constantes ou quase-constantes,
cardinalidade de colunas e unicidade de chaves primárias.
"""

from __future__ import annotations

from statistics import mean

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityFactor
from spark_eda.domain.entities.statistic import CategoricalStats
from spark_eda.domain.services.quality_factors import _score_severity, registrar
from spark_eda.domain.value_objects.severity import Severity

_UNIQUE_LOW_THRESHOLD = 0.5
_UNIQUE_HIGH_THRESHOLD = 0.99
_NEAR_DUPLICATE_THRESHOLD = 0.95
_LARGE_ROW_THRESHOLD = 100
_CARDINALITY_LOW = 0.01
_CARDINALITY_HIGH = 0.99


def _is_primary_key_candidate(column_name: str) -> bool:
    """Retorna ``True`` se o nome da coluna sugere que é uma chave primária."""
    normalized_name: str = column_name.lower().replace("_", "").replace("-", "")
    pk_patterns: tuple[str, ...] = (
        "id",
        "codigo",
        "cod",
        "chave",
        "pk",
        "primarykey",
        "uuid",
        "guid",
        "hash",
    )
    for pattern in pk_patterns:
        if normalized_name == pattern or normalized_name.endswith(pattern) or normalized_name.startswith(pattern):
            return True
    return False


def _duplicate_ratio(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de proporção de duplicatas.

    Utiliza o ``unique_ratio`` de colunas categóricas como proxy para
    a taxa de duplicatas no dataset.
    """
    unique_ratios: list[float] = []
    affected_columns: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, CategoricalStats):
            unique_ratios.append(stats.unique_ratio)
            if stats.unique_ratio < _UNIQUE_LOW_THRESHOLD:
                affected_columns.append(column_metadata.name)

    if not unique_ratios:
        return QualityFactor(
            name="Proporção de duplicatas",
            score=1.0,
            internal_weight=0.25,
            contribution=0.25,
            reason="Nenhuma coluna categórica disponível para estimativa de duplicatas.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    mean_uniqueness: float = mean(unique_ratios)
    score: float = mean_uniqueness

    return QualityFactor(
        name="Proporção de duplicatas",
        score=score,
        internal_weight=0.25,
        contribution=score * 0.25,
        reason=(
            f"Unique ratio médio de {mean_uniqueness:.1%} entre "
            f"{len(unique_ratios)} colunas categóricas. Valores próximos "
            f"de 1.0 indicam baixa duplicação."
        ),
        severity=_score_severity(score),
        affected_columns=affected_columns,
    )


def _pk_uniqueness(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de unicidade de chaves primárias.

    Identifica colunas candidatas a chave primária pelo nome e avalia
    seu ``unique_ratio``. Colunas sem estatísticas categóricas são
    ignoradas.
    """
    affected_columns: list[str] = []
    pks_found: int = 0
    pks_unique: int = 0

    for column_metadata in profile.columns:
        if _is_primary_key_candidate(column_metadata.name):
            pks_found += 1
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            stats = column_profile.stats
            if isinstance(stats, CategoricalStats) and stats.unique_ratio >= _UNIQUE_HIGH_THRESHOLD:
                pks_unique += 1
            else:
                affected_columns.append(column_metadata.name)

    if pks_found == 0:
        return QualityFactor(
            name="Unicidade de chaves primárias",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma coluna candidata a chave primária encontrada.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    score: float = pks_unique / pks_found

    return QualityFactor(
        name="Unicidade de chaves primárias",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(f"{pks_unique} de {pks_found} colunas candidatas a chave primária possuem unique ratio ≥ 99%."),
        severity=_score_severity(score),
        affected_columns=affected_columns,
    )


def _near_duplicates(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de quase-duplicatas.

    Identifica colunas categóricas cujo unique ratio está em uma
    faixa intermediária (entre 0.95 e 1.0), sugerindo a presença de
    valores muito próximos.
    """
    near_duplicate_columns: list[str] = []
    total_categorical: int = 0

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, CategoricalStats):
            total_categorical += 1
            if _NEAR_DUPLICATE_THRESHOLD <= stats.unique_ratio < 1.0:
                near_duplicate_columns.append(column_metadata.name)

    if total_categorical == 0:
        return QualityFactor(
            name="Quase-duplicatas",
            score=1.0,
            internal_weight=0.15,
            contribution=0.15,
            reason="Nenhuma coluna categórica disponível para análise.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    proportion: float = len(near_duplicate_columns) / total_categorical
    score: float = 1.0 - proportion

    return QualityFactor(
        name="Quase-duplicatas",
        score=score,
        internal_weight=0.15,
        contribution=score * 0.15,
        reason=(
            f"{len(near_duplicate_columns)} de {total_categorical} "
            f"colunas categóricas possuem unique ratio entre 0.95 e 1.0, "
            f"sugerindo potenciais quase-duplicatas."
        ),
        severity=_score_severity(score),
        affected_columns=near_duplicate_columns,
    )


def _constant_columns(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de colunas constantes.

    Colunas constantes possuem cardinalidade 1 (um único valor distinto).
    A pontuação é inversamente proporcional à fração de colunas
    constantes.
    """
    constant_columns_list: list[str] = []
    total_with_cardinality: int = 0

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, CategoricalStats):
            total_with_cardinality += 1
            if stats.cardinality == 1:
                constant_columns_list.append(column_metadata.name)

    if total_with_cardinality == 0:
        return QualityFactor(
            name="Colunas constantes",
            score=1.0,
            internal_weight=0.20,
            contribution=0.20,
            reason="Nenhuma coluna com cardinalidade disponível para análise.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    proportion_constants: float = len(constant_columns_list) / total_with_cardinality
    score: float = 1.0 - proportion_constants

    return QualityFactor(
        name="Colunas constantes",
        score=score,
        internal_weight=0.20,
        contribution=score * 0.20,
        reason=(
            f"{len(constant_columns_list)} de {total_with_cardinality} colunas possuem cardinalidade 1 (constantes)."
        ),
        severity=_score_severity(score),
        affected_columns=constant_columns_list,
    )


def _near_constant_columns(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de colunas quase-constantes.

    Colunas quase-constantes possuem cardinalidade muito baixa (2 ou 3)
    em relação ao total de linhas. A pontuação reflete a fração de
    colunas que se desviam deste padrão.
    """
    near_constant_list: list[str] = []
    total_with_cardinality: int = 0

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, CategoricalStats) and stats.cardinality >= 1:
            total_with_cardinality += 1
            if stats.cardinality in (2, 3) and profile.row_count > _LARGE_ROW_THRESHOLD:
                near_constant_list.append(column_metadata.name)

    if total_with_cardinality == 0:
        return QualityFactor(
            name="Colunas quase-constantes",
            score=1.0,
            internal_weight=0.10,
            contribution=0.10,
            reason="Nenhuma coluna com cardinalidade disponível para análise.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    proportion: float = len(near_constant_list) / total_with_cardinality
    score: float = 1.0 - proportion

    return QualityFactor(
        name="Colunas quase-constantes",
        score=score,
        internal_weight=0.10,
        contribution=score * 0.10,
        reason=(
            f"{len(near_constant_list)} de {total_with_cardinality} "
            f"colunas possuem cardinalidade 2 ou 3 em um dataset com "
            f"{profile.row_count} linhas."
        ),
        severity=_score_severity(score),
        affected_columns=near_constant_list,
    )


def _cardinality_factor(profile: DataProfile) -> QualityFactor:
    """Calcula o fator de cardinalidade geral.

    Avalia a razão média de valores distintos para o total de linhas
    em colunas categóricas. Valores muito baixos indicam repetição
    excessiva; valores muito altos podem indicar chaves.
    """
    cardinality_ratios: list[float] = []
    affected_columns: list[str] = []

    for column_metadata in profile.columns:
        column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
        stats = column_profile.stats
        if isinstance(stats, CategoricalStats) and profile.row_count > 0:
            ratio: float = stats.cardinality / profile.row_count
            cardinality_ratios.append(ratio)
            if ratio < _CARDINALITY_LOW or ratio > _CARDINALITY_HIGH:
                affected_columns.append(column_metadata.name)

    if not cardinality_ratios:
        return QualityFactor(
            name="Cardinalidade",
            score=1.0,
            internal_weight=0.10,
            contribution=0.10,
            reason="Nenhuma coluna categórica disponível para análise de cardinalidade.",
            severity=Severity.LOW,
            affected_columns=[],
        )

    mean_ratio: float = mean(cardinality_ratios)

    score = 1.0 - abs(0.5 - mean_ratio) * 2
    score = max(0.0, min(1.0, score))

    return QualityFactor(
        name="Cardinalidade",
        score=score,
        internal_weight=0.10,
        contribution=score * 0.10,
        reason=(
            f"Razão cardinalidade/linhas média de {mean_ratio:.4f} "
            f"entre {len(cardinality_ratios)} colunas. Ideal próximo de 0.5."
        ),
        severity=_score_severity(score),
        affected_columns=affected_columns,
    )


@registrar("uniqueness")
def calcular_score(profile: DataProfile) -> list[QualityFactor]:
    """Calcula todos os fatores para a dimensão **Unicidade**.

    Args:
        profile: Perfil completo do dataset.

    Returns:
        Lista de seis fatores de unicidade: proporção de duplicatas,
        unicidade de chaves primárias, quase-duplicatas, colunas
        constantes, colunas quase-constantes e cardinalidade.
    """
    return [
        _duplicate_ratio(profile),
        _pk_uniqueness(profile),
        _near_duplicates(profile),
        _constant_columns(profile),
        _near_constant_columns(profile),
        _cardinality_factor(profile),
    ]
