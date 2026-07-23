"""Presenter que converte DatasetAnalysis em EDAReport."""

from __future__ import annotations

from typing import Any

from spark_eda.application.dto.correlation_section import CorrelationEntry, CorrelationSection
from spark_eda.application.dto.distribution_section import (
    DistributionSection,
    FrequencyEntry,
    HistogramBin,
    TemporalPoint,
)
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.insights_section import InsightDTO, InsightsSection
from spark_eda.application.dto.outlier_section import OutlierSection, OutlierSummary
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.quality_section import (
    QualityDimensionReport,
    QualityFactorReport,
    QualityReport,
)
from spark_eda.application.dto.recommendations_section import (
    RecommendationDTO,
    RecommendationsSection,
)
from spark_eda.application.dto.schema_section import SchemaColumn, SchemaSection
from spark_eda.application.dto.stats_section import (
    BooleanStatsDTO,
    CategoricalStatsDTO,
    NumericStatsDTO,
    StatsSection,
    TemporalStatsDTO,
    TextStatsDTO,
)
from spark_eda.adapters.presenters.quality_presenter import QualityPresenter
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.distribution import (
    CategoricalDistribution,
    Distribution,
    NumericDistribution,
    TemporalDistribution,
)
from spark_eda.domain.entities.statistic import (
    BooleanStats,
    CategoricalStats,
    NumericStats,
    Statistic,
    TemporalStats,
    TextStats,
)
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.application.ports.output_presenter import OutputPresenter


class AnalysisPresenter(OutputPresenter):
    """Presenter que converte um ``DatasetAnalysis`` em um ``EDAReport``.

    Cada seção do relatório é construída a partir das entidades de domínio
    correspondentes, traduzindo tipos de domínio para strings e estruturando
    os dados para apresentação.
    """

    def present(self, analysis: DatasetAnalysis) -> EDAReport:
        """Converte a análise completa em um ``EDAReport``.

        Args:
            analysis: Análise exploratória completa com perfil,
                qualidade, correlações, insights e recomendações.

        Returns:
            ``EDAReport`` com todas as seções preenchidas.
        """
        overview: OverviewSection = self._build_overview(analysis)
        schema: SchemaSection = self._build_schema(analysis.profile)
        quality: QualityReport = QualityPresenter().present(analysis.quality)
        stats: StatsSection = self._build_stats(analysis.profile)
        distributions: DistributionSection = self._build_distributions(analysis.profile)
        correlations: CorrelationSection = self._build_correlations(analysis)
        outliers: OutlierSection = self._build_outliers(analysis.profile)
        insights: InsightsSection = self._build_insights(analysis)
        recommendations: RecommendationsSection = self._build_recommendations(analysis)

        return EDAReport(
            overview=overview,
            schema=schema,
            quality=quality,
            stats=stats,
            distributions=distributions,
            correlations=correlations,
            outliers=outliers,
            insights=insights,
            recommendations=recommendations,
        )

    def present_analysis(self, analysis: DatasetAnalysis) -> Any:
        """Implementa o contrato ``OutputPresenter.present_analysis``.

        Args:
            analysis: Análise exploratória a ser apresentada.

        Returns:
            ``EDAReport`` formatado.
        """
        return self.present(analysis)

    def present_quality(self, quality: Any) -> Any:
        """Implementa o contrato ``OutputPresenter.present_quality``.

        Delega para ``QualityPresenter``.

        Args:
            quality: Pontuação de qualidade a ser apresentada.

        Returns:
            ``QualityReport`` formatado.
        """
        return QualityPresenter().present_quality(quality)

    def _build_overview(self, analysis: DatasetAnalysis) -> OverviewSection:
        """Constrói a seção de visão geral."""
        profile: DataProfile = analysis.profile
        row_count: int = profile.row_count
        column_count: int = len(profile.columns)
        total_cells: int = row_count * column_count

        # Derive duplicates from the uniqueness dimension, if available
        duplicate_count: int = 0
        if "unicidade" in analysis.quality.dimensions:
            for factor in analysis.quality.dimensions["unicidade"].factors:
                if "duplicata" in factor.name.lower():
                    duplicate_count = int(factor.affected_columns[0]) if factor.affected_columns else 0
                    for word in factor.reason.split():
                        if word.isdigit():
                            duplicate_count = int(word)
                            break

        duplicate_ratio: float = duplicate_count / row_count if row_count > 0 else 0.0

        # Proportion of missing values
        total_null: int = sum(col.null_count for col in profile.columns)
        missing_ratio: float = total_null / total_cells if total_cells > 0 else 0.0

        # Size estimate (approximate by type)
        size_estimate: int = 0
        for col in profile.columns:
            if col.data_type in (DataType.INTEGER, DataType.LONG):
                size_estimate += row_count * 8
            elif col.data_type == DataType.DOUBLE:
                size_estimate += row_count * 8
            elif col.data_type == DataType.DECIMAL:
                size_estimate += row_count * 12
            elif col.data_type == DataType.BOOLEAN:
                size_estimate += row_count * 1
            elif col.data_type == DataType.DATE:
                size_estimate += row_count * 4
            elif col.data_type == DataType.TIMESTAMP:
                size_estimate += row_count * 8
            else:
                size_estimate += row_count * 50  # estimate for strings

        return OverviewSection(
            row_count=row_count,
            column_count=column_count,
            duplicate_count=duplicate_count,
            duplicate_ratio=duplicate_ratio,
            missing_ratio=missing_ratio,
            size_estimate=size_estimate,
        )

    def _build_schema(self, profile: DataProfile) -> SchemaSection:
        """Constrói a seção de esquema."""
        columns: list[SchemaColumn] = [
            SchemaColumn(
                name=col.name,
                type=col.data_type.value,
                nullable=col.nullable,
                inferred_type=col.inferred_type.value if col.inferred_type else None,
                null_count=col.null_count,
            )
            for col in profile.columns
        ]
        return SchemaSection(columns=columns)

    def _build_stats(self, profile: DataProfile) -> StatsSection:
        """Constrói a seção de estatísticas descritivas."""
        numeric: list[NumericStatsDTO] = []
        categorical: list[CategoricalStatsDTO] = []
        temporal: list[TemporalStatsDTO] = []
        text: list[TextStatsDTO] = []
        boolean: list[BooleanStatsDTO] = []

        for col in profile.columns:
            col_profile: ColumnProfile | None = profile.column_profiles.get(col.name)
            if col_profile is None or col_profile.stats is None:
                continue

            stats: Statistic = col_profile.stats
            col_name: str = col.name

            if isinstance(stats, NumericStats):
                numeric.append(
                    NumericStatsDTO(
                        column_name=col_name,
                        mean=stats.mean,
                        std=stats.std,
                        min=stats.min,
                        q25=stats.q25,
                        q50=stats.q50,
                        q75=stats.q75,
                        max=stats.max,
                        skewness=stats.skewness,
                        kurtosis=stats.kurtosis,
                    )
                )
            elif isinstance(stats, CategoricalStats):
                top_values: list[tuple[str, int]] = list(stats.value_counts.items())[:10]
                categorical.append(
                    CategoricalStatsDTO(
                        column_name=col_name,
                        cardinality=stats.cardinality,
                        mode=stats.mode,
                        unique_ratio=stats.unique_ratio,
                        top_values=top_values,
                    )
                )
            elif isinstance(stats, TemporalStats):
                temporal.append(
                    TemporalStatsDTO(
                        column_name=col_name,
                        min_date=stats.min_date,
                        max_date=stats.max_date,
                        range_days=stats.range_days,
                        gap_count=stats.gap_count,
                    )
                )
            elif isinstance(stats, TextStats):
                text.append(
                    TextStatsDTO(
                        column_name=col_name,
                        min_length=stats.min_length,
                        max_length=stats.max_length,
                        avg_length=stats.avg_length,
                        empty_ratio=stats.empty_ratio,
                    )
                )
            elif isinstance(stats, BooleanStats):
                boolean.append(
                    BooleanStatsDTO(
                        column_name=col_name,
                        true_count=stats.true_count,
                        false_count=stats.false_count,
                        true_ratio=stats.true_ratio,
                    )
                )

        return StatsSection(
            numeric=numeric,
            categorical=categorical,
            temporal=temporal,
            text=text,
            boolean=boolean,
        )

    def _build_distributions(self, profile: DataProfile) -> DistributionSection:
        """Constrói a seção de distribuições."""
        histograms: dict[str, list[HistogramBin]] = {}
        frequencies: dict[str, list[FrequencyEntry]] = {}
        temporal_charts: dict[str, list[TemporalPoint]] = {}

        for col in profile.columns:
            col_profile: ColumnProfile | None = profile.column_profiles.get(col.name)
            if col_profile is None or col_profile.distribution is None:
                continue

            dist: Distribution = col_profile.distribution
            if isinstance(dist, NumericDistribution):
                histograms[col.name] = [
                    HistogramBin(lower=lower, upper=upper, count=count)
                    for lower, upper, count in dist.bins
                ]
            elif isinstance(dist, CategoricalDistribution):
                frequencies[col.name] = [
                    FrequencyEntry(label=cat, count=count)
                    for cat, count in dist.categories
                ]
            elif isinstance(dist, TemporalDistribution):
                temporal_charts[col.name] = [
                    TemporalPoint(period=period, count=count)
                    for period, count in dist.periods
                ]

        return DistributionSection(
            histograms=histograms,
            frequencies=frequencies,
            temporal_charts=temporal_charts,
        )

    def _build_correlations(self, analysis: DatasetAnalysis) -> CorrelationSection:
        """Constrói a seção de correlações."""
        entries: list[CorrelationEntry] = [
            CorrelationEntry(
                column_a=c.column_a,
                column_b=c.column_b,
                method=c.method.value,
                value=c.value,
            )
            for c in analysis.correlations
        ]

        # Build matrix from entries
        all_columns: list[str] = sorted({e.column_a for e in entries} | {e.column_b for e in entries})
        matrix: dict[str, dict[str, float]] = {c: {} for c in all_columns}
        for c in all_columns:
            for c2 in all_columns:
                matrix[c][c2] = 0.0

        for e in entries:
            if e.column_a in matrix and e.column_b in matrix[e.column_a]:
                matrix[e.column_a][e.column_b] = e.value
                matrix[e.column_b][e.column_a] = e.value
            matrix[e.column_a][e.column_a] = 1.0
            matrix[e.column_b][e.column_b] = 1.0

        method: str = analysis.correlations[0].method.value if analysis.correlations else "\u2014"

        return CorrelationSection(
            correlations=entries,
            matrix=matrix,
            method=method,
        )

    def _build_outliers(self, profile: DataProfile) -> OutlierSection:
        """Constrói a seção de outliers."""
        summaries: list[OutlierSummary] = []
        for col in profile.columns:
            col_profile: ColumnProfile | None = profile.column_profiles.get(col.name)
            if col_profile is None or col_profile.outlier is None:
                continue
            outlier: OutlierInfo = col_profile.outlier
            summaries.append(
                OutlierSummary(
                    column_name=col.name,
                    method=outlier.method.value,
                    count=outlier.count,
                    ratio=outlier.ratio,
                    bounds_lower=outlier.bounds_lower,
                    bounds_upper=outlier.bounds_upper,
                )
            )
        return OutlierSection(outliers=summaries)

    def _build_insights(self, analysis: DatasetAnalysis) -> InsightsSection:
        """Constrói a seção de insights."""
        insights: list[InsightDTO] = [
            InsightDTO(
                category=insight.category.value,
                severity=insight.severity.value,
                column=insight.column,
                message=insight.message,
                metric_value=insight.metric_value,
            )
            for insight in analysis.insights
        ]
        return InsightsSection(insights=insights)

    def _build_recommendations(self, analysis: DatasetAnalysis) -> RecommendationsSection:
        """Constrói a seção de recomendações."""
        recommendations: list[RecommendationDTO] = [
            RecommendationDTO(
                category=rec.category.value,
                priority=rec.priority,
                column=rec.column,
                message=rec.message,
                action=rec.action,
            )
            for rec in analysis.recommendations
        ]
        return RecommendationsSection(recommendations=recommendations)
