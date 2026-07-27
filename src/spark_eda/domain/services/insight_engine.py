"""Motor de geração de insights.

Analisa o perfil do dataset e a pontuação de qualidade para produzir
uma lista de :class:`~spark_eda.domain.entities.insight.Insight` com
descobertas relevantes sobre os dados.
"""

from __future__ import annotations

from statistics import mean

from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.entities.statistic import CategoricalStats, NumericStats
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.severity import Severity

_NULL_THRESHOLD: float = 0.30
_SKEWNESS_THRESHOLD: float = 1.0
_DUPLICATE_THRESHOLD: float = 0.05
_OUTLIER_THRESHOLD: float = 0.10
_ZERO_THRESHOLD: float = 0.05

_NULL_HIGH_SEVERITY = 0.50
_NULL_MEDIUM_SEVERITY = 0.40

_SKEW_HIGH_SEVERITY = 2.0
_SKEW_MEDIUM_SEVERITY = 1.5

_HIGH_UNIQUE_RATIO = 0.95
_NEAR_UNIQUE_RATIO = 0.99

_NEAR_CONSTANT_CARDINALITY = 3
_LARGE_ROW_COUNT = 100

_DUP_HIGH_SEVERITY = 0.20
_DUP_MEDIUM_SEVERITY = 0.10

_OUTLIER_HIGH_SEVERITY = 0.25
_OUTLIER_MEDIUM_SEVERITY = 0.15

_SCORE_HIGH_SEVERITY = 0.3
_SCORE_MEDIUM_SEVERITY = 0.6


class InsightEngine:
    """Motor de geração de insights, sem estado.

    Aplica regras de negócio sobre um :class:`DataProfile` e um
    :class:`QualityScore` para identificar padrões, anomalias
    e oportunidades de melhoria nos dados.
    """

    @staticmethod
    def _insight_null_columns(
        profile: DataProfile,
    ) -> list[Insight]:
        """Gera insights sobre colunas com alta proporção de nulos.

        Regra: null_count / total > 30 %.
        """
        insights: list[Insight] = []

        for column_metadata in profile.columns:
            total_column: int = column_metadata.null_count + column_metadata.non_null_count
            if total_column == 0:
                continue

            null_ratio: float = column_metadata.null_count / total_column
            if null_ratio > _NULL_THRESHOLD:
                severity: Severity
                if null_ratio > _NULL_HIGH_SEVERITY:
                    severity = Severity.CRITICAL
                elif null_ratio > _NULL_MEDIUM_SEVERITY:
                    severity = Severity.HIGH
                else:
                    severity = Severity.MEDIUM

                insights.append(Insight(
                    category=InsightCategory.NULLS,
                    severity=severity,
                    column=column_metadata.name,
                    message=(
                        f"A coluna '{column_metadata.name}' possui "
                        f"{null_ratio:.1%} de valores nulos "
                        f"({column_metadata.null_count} de {total_column} registros)."
                    ),
                    metric_value=round(null_ratio, 4),
                ))

        return insights

    @staticmethod
    def _insight_skewness(
        profile: DataProfile,
    ) -> list[Insight]:
        """Gera insights sobre assimetria em colunas numéricas.

        Regra: |skewness| > 1.0 indica assimetria significativa.
        """
        insights: list[Insight] = []

        for column_metadata in profile.columns:
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            stats = column_profile.stats
            if not isinstance(stats, NumericStats):
                continue

            skewness_abs: float = abs(stats.skewness)
            if skewness_abs > _SKEWNESS_THRESHOLD:
                direction: str = "à direita" if stats.skewness > 0 else "à esquerda"

                severity: Severity
                if skewness_abs > _SKEW_HIGH_SEVERITY:
                    severity = Severity.HIGH
                elif skewness_abs > _SKEW_MEDIUM_SEVERITY:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

                insights.append(Insight(
                    category=InsightCategory.SKEWNESS,
                    severity=severity,
                    column=column_metadata.name,
                    message=(
                        f"A coluna '{column_metadata.name}' apresenta "
                        f"assimetria de {stats.skewness:.2f} "
                        f"(inclinação {direction}), sugerindo distribuição "
                        f"não normal."
                    ),
                    metric_value=round(stats.skewness, 4),
                ))

        return insights

    @staticmethod
    def _insight_cardinality(
        profile: DataProfile,
    ) -> list[Insight]:
        """Gera insights sobre cardinalidade alta ou atípica.

        Regra: unique_ratio > 0.95 em colunas categóricas.
        """
        insights: list[Insight] = []

        for column_metadata in profile.columns:
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            stats = column_profile.stats
            if not isinstance(stats, CategoricalStats):
                continue

            if stats.unique_ratio > _HIGH_UNIQUE_RATIO and profile.row_count > 0:
                severity: Severity
                severity = Severity.MEDIUM if stats.unique_ratio >= _NEAR_UNIQUE_RATIO else Severity.LOW

                insights.append(Insight(
                    category=InsightCategory.CARDINALITY,
                    severity=severity,
                    column=column_metadata.name,
                    message=(
                        f"A coluna '{column_metadata.name}' possui "
                        f"{stats.cardinality} valores distintos "
                        f"(unique ratio de {stats.unique_ratio:.1%}), "
                        f"podendo ser candidata a chave."
                    ),
                    metric_value=round(stats.unique_ratio, 4),
                ))

        return insights

    @staticmethod
    def _insight_constant_columns(
        profile: DataProfile,
    ) -> list[Insight]:
        """Gera insights sobre colunas constantes.

        Regra: cardinalidade == 1 ou cardinalidade muito baixa (2-3)
        com um grande número de registros.
        """
        insights: list[Insight] = []

        for column_metadata in profile.columns:
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            stats = column_profile.stats
            if not isinstance(stats, CategoricalStats):
                continue

            if stats.cardinality == 1:
                insights.append(Insight(
                    category=InsightCategory.CONSTANT,
                    severity=Severity.MEDIUM,
                    column=column_metadata.name,
                    message=(
                        f"A coluna '{column_metadata.name}' é constante "
                        f"(cardinalidade 1 — todos os registros possuem "
                        f"o mesmo valor)."
                    ),
                    metric_value=1.0,
                ))
            elif stats.cardinality <= _NEAR_CONSTANT_CARDINALITY and profile.row_count > _LARGE_ROW_COUNT:
                insights.append(Insight(
                    category=InsightCategory.NEAR_CONSTANT,
                    severity=Severity.LOW,
                    column=column_metadata.name,
                    message=(
                        f"A coluna '{column_metadata.name}' possui "
                        f"apenas {stats.cardinality} valores distintos "
                        f"para {profile.row_count} registros, "
                        f"sendo praticamente constante."
                    ),
                    metric_value=round(stats.cardinality / profile.row_count, 4),
                ))

        return insights

    @staticmethod
    def _insight_duplicates(
        profile: DataProfile,
    ) -> list[Insight]:
        """Gera insights sobre duplicatas.

        Regra: unique_ratio < 0.95 em colunas que não são chaves.
        """
        insights: list[Insight] = []

        unique_ratios: list[float] = []
        for column_metadata in profile.columns:
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            stats = column_profile.stats
            if isinstance(stats, CategoricalStats):
                unique_ratios.append(stats.unique_ratio)

        if unique_ratios and profile.row_count > 0:
            mean_unique: float = mean(unique_ratios)
            estimated_duplicate_ratio: float = 1.0 - mean_unique

            if estimated_duplicate_ratio > _DUPLICATE_THRESHOLD:
                severity: Severity
                if estimated_duplicate_ratio > _DUP_HIGH_SEVERITY:
                    severity = Severity.HIGH
                elif estimated_duplicate_ratio > _DUP_MEDIUM_SEVERITY:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

                insights.append(Insight(
                    category=InsightCategory.DUPLICATES,
                    severity=severity,
                    column=None,
                    message=(
                        f"Taxa estimada de duplicatas de "
                        f"{estimated_duplicate_ratio:.1%} com base no "
                        f"unique ratio médio de {len(unique_ratios)} "
                        f"colunas categóricas."
                    ),
                    metric_value=round(estimated_duplicate_ratio, 4),
                ))

        return insights

    @staticmethod
    def _insight_outliers(
        profile: DataProfile,
    ) -> list[Insight]:
        """Gera insights sobre outliers em colunas numéricas.

        Regra: proporção de outliers > 10 %.
        """
        insights: list[Insight] = []

        for column_metadata in profile.columns:
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            outlier_info = column_profile.outlier
            if outlier_info is None:
                continue

            if outlier_info.ratio > _OUTLIER_THRESHOLD:
                severity: Severity
                if outlier_info.ratio > _OUTLIER_HIGH_SEVERITY:
                    severity = Severity.HIGH
                elif outlier_info.ratio > _OUTLIER_MEDIUM_SEVERITY:
                    severity = Severity.MEDIUM
                else:
                    severity = Severity.LOW

                bounds_info: str = ""
                if outlier_info.bounds_lower is not None or outlier_info.bounds_upper is not None:
                    bounds_info = (
                        f" (limites: [{outlier_info.bounds_lower or '-∞'}, "
                        f"{outlier_info.bounds_upper or '∞'}])"
                    )

                insights.append(Insight(
                    category=InsightCategory.OUTLIERS,
                    severity=severity,
                    column=column_metadata.name,
                    message=(
                        f"A coluna '{column_metadata.name}' possui "
                        f"{outlier_info.ratio:.1%} de outliers "
                        f"({outlier_info.count} registros, método "
                        f"{outlier_info.method.value}){bounds_info}."
                    ),
                    metric_value=round(outlier_info.ratio, 4),
                ))

        return insights

    @staticmethod
    def _insight_zero_values(
        profile: DataProfile,
    ) -> list[Insight]:
        """Gera insights sobre valores zero em colunas onde são atípicos.

        Regra: colunas com "zero" no nome ou colunas numéricas onde
        o mínimo é 0 e a proporção estimada de zeros é relevante.
        """
        insights: list[Insight] = []

        for column_metadata in profile.columns:
            column_profile: ColumnProfile = profile.column_profiles[column_metadata.name]
            stats = column_profile.stats
            if not isinstance(stats, NumericStats):
                continue

            normalized_name: str = column_metadata.name.lower()

            if stats.min == 0.0 and (normalized_name.startswith("zero") or "zerado" in normalized_name):
                insights.append(Insight(
                    category=InsightCategory.ZERO_VALUES,
                    severity=Severity.MEDIUM,
                    column=column_metadata.name,
                    message=(
                        f"A coluna '{column_metadata.name}' possui "
                        f"valores zerados ou indicação de zeragem "
                        f"(mínimo = 0)."
                    ),
                    metric_value=0.0,
                ))

        return insights

    @staticmethod
    def _insight_business_pattern(
        quality: QualityScore,
    ) -> list[Insight]:
        """Gera insights sobre violações de regras de negócio.

        Analisa fatores da dimensão 'accuracy' em busca de
        violações de regras de negócio identificadas.
        """
        insights: list[Insight] = []

        accuracy_dimension = quality.dimensions.get("accuracy")
        if accuracy_dimension is None:
            return insights

        for factor in accuracy_dimension.factors:
            if factor.name == "Regras de negócio" and factor.score < 1.0:
                for column in factor.affected_columns:
                    severity: Severity
                    if factor.score < _SCORE_HIGH_SEVERITY:
                        severity = Severity.HIGH
                    elif factor.score < _SCORE_MEDIUM_SEVERITY:
                        severity = Severity.MEDIUM
                    else:
                        severity = Severity.LOW

                    insights.append(Insight(
                        category=InsightCategory.BUSINESS_PATTERN,
                        severity=severity,
                        column=column,
                        message=f"Regra de negócio violada na coluna '{column}': {factor.reason}",
                        metric_value=round(factor.score, 4),
                    ))

        return insights

    def generate(
        self,
        profile: DataProfile,
        quality: QualityScore,
    ) -> list[Insight]:
        """Gera a lista completa de insights para o dataset.

        Aplica todas as regras de análise disponíveis:

        * Proporção de nulos por coluna (> 30 %)
        * Assimetria da distribuição (|skewness| > 1.0)
        * Cardinalidade alta (unique ratio > 0.95)
        * Colunas constantes e quase-constantes
        * Taxa estimada de duplicatas
        * Outliers por coluna (> 10 %)
        * Valores zero atípicos
        * Violações de regras de negócio

        Args:
            profile: Perfil completo do dataset.
            quality: Pontuação de qualidade consolidada.

        Returns:
            Lista de :class:`Insight` ordenada por severidade
            (críticos primeiro).
        """
        insights: list[Insight] = []
        insights.extend(self._insight_null_columns(profile))
        insights.extend(self._insight_skewness(profile))
        insights.extend(self._insight_cardinality(profile))
        insights.extend(self._insight_constant_columns(profile))
        insights.extend(self._insight_duplicates(profile))
        insights.extend(self._insight_outliers(profile))
        insights.extend(self._insight_zero_values(profile))
        insights.extend(self._insight_business_pattern(quality))

        severity_order: dict[Severity, int] = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
        }
        insights.sort(key=lambda insight: severity_order.get(insight.severity, 4))

        return insights
