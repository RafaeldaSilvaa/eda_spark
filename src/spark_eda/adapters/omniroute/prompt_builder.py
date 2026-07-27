"""Constrói prompts para análise de relatórios EDA pelo OmniRoute."""

from __future__ import annotations

from spark_eda.application.dto.correlation_section import CorrelationEntry
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.outlier_section import OutlierSection
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.quality_section import QualityReport
from spark_eda.application.dto.schema_section import SchemaSection
from spark_eda.application.dto.stats_section import (
    StatsSection,
)

_SYSTEM_PROMPT: str = (
    "You are a staff-level data engineer/analyst with 15+ years of experience. "
    "You are an expert at exploratory data analysis, statistical inference, "
    "and identifying non-obvious patterns in structured datasets. "
    "You communicate clearly and concisely, always framing data findings "
    "in business context. You identify data quality issues, suggest testable "
    "hypotheses, and extract actionable business implications from raw statistics. "
    "You think critically — you do not fabricate patterns where none exist."
)

_JSON_INSTRUCTION: str = (
    "Respond ONLY with a valid JSON object using the following keys: "
    '"overview", "schema", "quality", "stats", "distributions", '
    '"correlations", "outliers", "insights", "recommendations", '
    'and "executive_analysis". '
    "Each key must map to a string with your commentary for that section, "
    "or null if there is nothing noteworthy. "
    "The executive_analysis key must contain a cross-cutting synthesis "
    "identifying patterns that span multiple sections. "
    "Keep each commentary concise (2-4 sentences per section), "
    "and the executive analysis at most 6 sentences."
)


class PromptBuilder:
    """Constrói prompts estruturados para análise via OmniRoute."""

    @staticmethod
    def build(report: EDAReport) -> str:
        """Serializa um ``EDAReport`` em um prompt de texto estruturado.

        Args:
            report: Relatório EDA completo com todas as 9 seções.

        Returns:
            Prompt formatado para envio ao OmniRoute.
        """
        sections: list[str] = []
        sections.append("=== EDA Report Data ===\n")
        sections.append(PromptBuilder._build_overview_section(report.overview))
        sections.append(PromptBuilder._build_schema_section(report.schema))
        sections.append(PromptBuilder._build_quality_section(report.quality))
        sections.append(PromptBuilder._build_stats_section(report.stats))
        sections.append(PromptBuilder._build_distribution_summary(report))
        sections.append(PromptBuilder._build_correlation_summary(report))
        sections.append(PromptBuilder._build_outlier_summary(report.outliers))
        sections.append(PromptBuilder._build_insights_summary(report))
        sections.append(PromptBuilder._build_recommendations_summary(report))
        sections.append(f"\n{_JSON_INSTRUCTION}")

        return "\n".join(sections)

    @staticmethod
    def _build_overview_section(overview: OverviewSection) -> str:
        lines: list[str] = ["## Dataset Overview"]
        lines.append(f"  Rows: {overview.row_count}")
        lines.append(f"  Columns: {overview.column_count}")
        lines.append(f"  Duplicates: {overview.duplicate_count} ({overview.duplicate_ratio:.2%})")
        lines.append(f"  Missing ratio: {overview.missing_ratio:.2%}")
        lines.append(f"  Estimated size: {overview.size_estimate} bytes")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_schema_section(schema: SchemaSection) -> str:
        lines: list[str] = ["## Schema"]
        for col in schema.columns:
            inferred: str = f" (inferred: {col.inferred_type})" if col.inferred_type else ""
            nullable: str = "nullable" if col.nullable else "required"
            lines.append(
                f"  - {col.name}: {col.type} ({nullable}, nulls={col.null_count}){inferred}"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_quality_section(quality: QualityReport) -> str:
        lines: list[str] = ["## Data Quality"]
        lines.append(f"  Overall score: {quality.overall:.1f}/100")
        if quality.dimensions:
            lines.append("  Dimensions:")
            for dim in quality.dimensions:
                lines.append(f"    - {dim.name}: {dim.score:.1f} (weight={dim.weight})")
        if quality.top_penalizers:
            lines.append("  Top penalizers:")
            for pen in quality.top_penalizers:
                lines.append(f"    - {pen.name} ({pen.severity}): score={pen.score:.2f}")
                lines.append(f"      {pen.reason}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_stats_section(stats: StatsSection) -> str:
        lines: list[str] = ["## Descriptive Statistics"]
        if stats.numeric:
            lines.append("  Numeric columns:")
            for n in stats.numeric:
                lines.append(
                    f"    - {n.column_name}: mean={n.mean:.4g}, std={n.std:.4g}, "
                    f"range=[{n.min:.4g}, {n.max:.4g}], "
                    f"skewness={n.skewness:.4g}, kurtosis={n.kurtosis:.4g}"
                )
        if stats.categorical:
            lines.append("  Categorical columns:")
            for c in stats.categorical:
                top: str = ", ".join(f"{v}:{c}" for v, c in c.top_values[:5])
                lines.append(
                    f"    - {c.column_name}: cardinality={c.cardinality}, "
                    f"mode={c.mode or 'N/A'}, unique_ratio={c.unique_ratio:.2%}"
                )
                if top:
                    lines.append(f"      top: {top}")
        if stats.temporal:
            lines.append("  Temporal columns:")
            for t in stats.temporal:
                lines.append(
                    f"    - {t.column_name}: [{t.min_date} .. {t.max_date}], "
                    f"range={t.range_days}d, gaps={t.gap_count}"
                )
        if stats.text:
            lines.append("  Text columns:")
            for txt in stats.text:
                lines.append(
                    f"    - {txt.column_name}: len=[{txt.min_length}..{txt.max_length}], "
                    f"avg={txt.avg_length:.1f}, empty_ratio={txt.empty_ratio:.2%}"
                )
        if stats.boolean:
            lines.append("  Boolean columns:")
            for b in stats.boolean:
                lines.append(
                    f"    - {b.column_name}: true={b.true_count}, "
                    f"false={b.false_count}, true_ratio={b.true_ratio:.2%}"
                )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_distribution_summary(report: EDAReport) -> str:
        lines: list[str] = ["## Distributions"]
        dist = report.distributions
        if dist.histograms:
            for col_name, bins in dist.histograms.items():
                if bins:
                    values: list[float] = [b.count for b in bins]
                    max_count: float = max(values)
                    bins_str: str = ", ".join(
                        f"[{b.lower:.4g}..{b.upper:.4g}]:{b.count}" for b in bins[:5]
                    )
                    suffix: str = " (+more)" if len(bins) > 5 else ""  # noqa: PLR2004
                    lines.append(f"  - {col_name}: {len(bins)} bins, peak={max_count}{suffix}")
                    lines.append(f"    bins: {bins_str}")
        if dist.frequencies:
            for col_name, entries in dist.frequencies.items():
                if entries:
                    lines.append(
                        f"  - {col_name}: {len(entries)} categories, "
                        f"top={entries[0].label} ({entries[0].count})"
                    )
        if dist.temporal_charts:
            for col_name, points in dist.temporal_charts.items():
                if points:
                    lines.append(
                        f"  - {col_name}: {len(points)} periods, "
                        f"[{points[0].period}..{points[-1].period}]"
                    )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_correlation_summary(report: EDAReport) -> str:
        lines: list[str] = ["## Correlations"]
        corr = report.correlations
        lines.append(f"  Method: {corr.method}")
        if corr.correlations:
            strong: list[CorrelationEntry] = [e for e in corr.correlations if abs(e.value) >= 0.5]  # noqa: PLR2004
            if strong:
                lines.append("  Strong correlations (|r| >= 0.5):")
                for e in strong:
                    lines.append(f"    - {e.column_a} x {e.column_b}: {e.value:.4f}")
            else:
                lines.append("  No strong correlations found.")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_outlier_summary(outliers: OutlierSection) -> str:
        lines: list[str] = ["## Outliers"]
        if outliers.outliers:
            for o in outliers.outliers:
                bounds: str = (
                    f" bounds=[{o.bounds_lower:.4g}..{o.bounds_upper:.4g}]"
                    if o.bounds_lower is not None and o.bounds_upper is not None
                    else ""
                )
                lines.append(
                    f"  - {o.column_name}: {o.count} ({o.ratio:.2%}) "
                    f"method={o.method}{bounds}"
                )
        else:
            lines.append("  No outliers detected.")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_insights_summary(report: EDAReport) -> str:
        lines: list[str] = ["## Insights"]
        if report.insights.insights:
            for ins in report.insights.insights:
                col: str = f" [{ins.column}]" if ins.column else ""
                metric: str = f" ({ins.metric_value:.4g})" if ins.metric_value is not None else ""
                lines.append(f"  [{ins.category}] ({ins.severity}){col}: {ins.message}{metric}")
        else:
            lines.append("  No insights generated.")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _build_recommendations_summary(report: EDAReport) -> str:
        lines: list[str] = ["## Recommendations"]
        if report.recommendations.recommendations:
            for rec in report.recommendations.recommendations:
                col: str = f" [{rec.column}]" if rec.column else ""
                lines.append(
                    f"  P{rec.priority} [{rec.category}]{col}: "
                    f"{rec.message} -> {rec.action}"
                )
        else:
            lines.append("  No recommendations.")
        return "\n".join(lines) + "\n"
