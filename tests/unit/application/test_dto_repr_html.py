from __future__ import annotations

"""Testes de apresentação (_repr_html_, __str__) para todos os DTOs.

Cobre cada método de apresentação dos DTOs que estava faltando
no relatório de cobertura, incluindo branches de helpers.
"""

from spark_eda.application.dto.correlation_section import (
    _correlation_color,
    _correlation_symbol,
    CorrelationEntry,
    CorrelationSection,
)
from spark_eda.application.dto.distribution_section import (
    _truncate_text,
    DistributionSection,
    HistogramBin,
    FrequencyEntry,
    TemporalPoint,
)
from spark_eda.application.dto.insights_section import (
    _severity_color as ins_severity_color,
    _severity_icon,
    _severity_marker,
    InsightDTO,
    InsightsSection,
)
from spark_eda.application.dto.outlier_section import (
    _outlier_severity,
    _severity_color as out_severity_color,
    _severity_emoji,
    OutlierSummary,
    OutlierSection,
)
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.recommendations_section import (
    _priority_color,
    _priority_label,
    _priority_marker,
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


# =========================================================================
# OVERVIEW
# =========================================================================

class TestOverviewSection:
    def test_repr_html(self) -> None:
        section = OverviewSection(
            row_count=1500, column_count=25,
            duplicate_count=30, duplicate_ratio=0.02,
            missing_ratio=0.05, size_estimate=2_000_000,
        )
        html = section._repr_html_()
        assert "Rows" in html
        assert "Columns" in html
        assert "Duplicates" in html
        assert "Missing" in html
        assert "Est. Size" in html

    def test_str(self) -> None:
        section = OverviewSection(
            row_count=1500, column_count=25,
            duplicate_count=30, duplicate_ratio=0.02,
            missing_ratio=0.05, size_estimate=2_000_000,
        )
        result = str(section)
        assert "Overview" in result
        assert "1.500" in result or "1500" in result


# =========================================================================
# SCHEMA
# =========================================================================

class TestSchemaSection:
    def test_repr_html(self) -> None:
        cols = [
            SchemaColumn("id", "integer", False, None, 0),
            SchemaColumn("nome", "string", True, None, 5),
        ]
        section = SchemaSection(columns=cols)
        html = section._repr_html_()
        assert "id" in html
        assert "nome" in html
        assert "integer" in html
        assert "string" in html

    def test_str(self) -> None:
        cols = [
            SchemaColumn("id", "integer", False, None, 0),
            SchemaColumn("nome", "string", True, None, 5),
        ]
        section = SchemaSection(columns=cols)
        result = str(section)
        assert "Schema" in result
        assert "id" in result
        assert "nome" in result

    def test_str_empty(self) -> None:
        """Nenhuma coluna → mensagem '(no columns)' (linha 73)."""
        section = SchemaSection(columns=[])
        result = str(section)
        assert "no columns" in result

    def test_schema_column_repr(self) -> None:
        col = SchemaColumn("id", "integer", False, None, 0)
        r = repr(col)
        assert "SchemaColumn" in r
        assert "id" in r


# =========================================================================
# STATS
# =========================================================================

class TestStatsSection:
    def _make_full_section(self) -> StatsSection:
        return StatsSection(
            numeric=[
                NumericStatsDTO("renda", 5000.0, 1500.0, 1000.0, 3000.0, 4500.0, 6000.0, 10000.0, 0.5, 2.0),
                NumericStatsDTO("idade", 35.0, 10.0, 18.0, 25.0, 33.0, 42.0, 65.0, 0.2, -0.5),
            ],
            categorical=[
                CategoricalStatsDTO("cat", 3, "A", 0.95, [("A", 50), ("B", 30), ("C", 20)]),
            ],
            temporal=[
                TemporalStatsDTO("dt", "2024-01-01", "2024-12-31", 365, 0),
            ],
            text=[
                TextStatsDTO("desc", 5, 200, 100.0, 0.02),
            ],
            boolean=[
                BooleanStatsDTO("flag", 60, 40, 0.6),
            ],
        )

    def test_repr_html_full(self) -> None:
        section = self._make_full_section()
        html = section._repr_html_()
        assert "Numeric" in html
        assert "Categorical" in html
        assert "Temporal" in html
        assert "Text" in html
        assert "Boolean" in html
        assert "renda" in html
        assert "idade" in html
        assert "cat" in html
        assert "dt" in html
        assert "desc" in html
        assert "flag" in html

    def test_repr_html_empty(self) -> None:
        """Nenhuma estatística → mensagem informativa."""
        section = StatsSection(numeric=[], categorical=[], temporal=[], text=[], boolean=[])
        html = section._repr_html_()
        assert "No statistics" in html

    def test_str_full(self) -> None:
        section = self._make_full_section()
        result = str(section)
        assert "Statistics" in result
        assert "Numeric:" in result
        assert "Categorical:" in result
        assert "Temporal:" in result
        assert "Text:" in result
        assert "Boolean:" in result
        assert "renda" in result

    def test_str_partial(self) -> None:
        """Apenas seções com dados aparecem no __str__."""
        section = StatsSection(
            numeric=[NumericStatsDTO("x", 1.0, 0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 0.0, -1.0)],
            categorical=[], temporal=[], text=[], boolean=[],
        )
        result = str(section)
        assert "Numeric:" in result
        assert "Categorical:" not in result
        assert "Temporal:" not in result
        assert "Text:" not in result
        assert "Boolean:" not in result

    def test_str_only_categorical(self) -> None:
        """__str__ sem dados numéricos → branch 308->317."""
        section = StatsSection(
            numeric=[],
            categorical=[CategoricalStatsDTO("cat", 3, "A", 0.95, [("A", 50)])],
            temporal=[], text=[], boolean=[],
        )
        result = str(section)
        assert "Numeric:" not in result
        assert "Categorical:" in result


# =========================================================================
# CORRELATION
# =========================================================================

class TestCorrelationSection:
    def test_correlation_color_branches(self) -> None:
        assert _correlation_color(0.1) == "#64748b"  # abs < 0.3
        assert _correlation_color(0.4) == "#2563eb"  # 0.3 <= abs < 0.6, positive
        assert _correlation_color(-0.4) == "#dc2626"  # negative
        assert _correlation_color(0.7) == "#1d4ed8"  # abs >= 0.6, positive
        assert _correlation_color(-0.7) == "#b91c1c"  # abs >= 0.6, negative

    def test_correlation_symbol_branches(self) -> None:
        assert _correlation_symbol(0.05) == " "
        assert _correlation_symbol(0.2) == "."
        assert _correlation_symbol(0.4) == "o"
        assert _correlation_symbol(0.6) == "O"
        assert _correlation_symbol(0.8) == "@"

    def test_repr_html(self) -> None:
        section = CorrelationSection(
            correlations=[
                CorrelationEntry("a", "b", "pearson", 0.85),
                CorrelationEntry("a", "c", "pearson", -0.4),
            ],
            matrix={"a": {"a": 1.0, "b": 0.85, "c": -0.4}, "b": {"a": 0.85, "b": 1.0, "c": 0.1}, "c": {"a": -0.4, "b": 0.1, "c": 1.0}},
            method="pearson",
        )
        html = section._repr_html_()
        assert "pearson" in html
        assert "a" in html
        assert "b" in html

    def test_repr_html_empty(self) -> None:
        """Matriz vazia → mensagem (linha 68)."""
        section = CorrelationSection(correlations=[], matrix={}, method="pearson")
        html = section._repr_html_()
        assert "No correlations" in html

    def test_str(self) -> None:
        section = CorrelationSection(
            correlations=[CorrelationEntry("a", "b", "pearson", 0.85)],
            matrix={"a": {"a": 1.0, "b": 0.85}, "b": {"a": 0.85, "b": 1.0}},
            method="pearson",
        )
        result = str(section)
        assert "Correlations" in result

    def test_str_empty(self) -> None:
        """Matriz vazia em __str__ (linha 111)."""
        section = CorrelationSection(correlations=[], matrix={}, method="pearson")
        result = str(section)
        assert "empty" in result

    def test_correlation_entry_repr(self) -> None:
        entry = CorrelationEntry("a", "b", "pearson", 0.85)
        r = repr(entry)
        assert "CorrelationEntry" in r


# =========================================================================
# DISTRIBUTION
# =========================================================================

class TestDistributionSection:
    def test_repr_html_with_all_types(self) -> None:
        section = DistributionSection(
            histograms={"valor": [HistogramBin(0.0, 10.0, 50), HistogramBin(10.0, 20.0, 30)]},
            frequencies={"cat": [FrequencyEntry("A", 40), FrequencyEntry("B", 20)]},
            temporal_charts={"dt": [TemporalPoint("2024-01", 100), TemporalPoint("2024-02", 80)]},
        )
        html = section._repr_html_()
        assert "valor" in html
        assert "cat" in html
        assert "dt" in html
        # Verifica que os nomes das colunas aparecem como cabeçalho
        assert "50" in html
        assert "40" in html
        assert "100" in html

    def test_repr_html_empty(self) -> None:
        section = DistributionSection(histograms={}, frequencies={}, temporal_charts={})
        html = section._repr_html_()
        assert "No distributions" in html

    def test_repr_html_empty_bins_skipped(self) -> None:
        section = DistributionSection(
            histograms={"vazia": []},
            frequencies={},
            temporal_charts={},
        )
        html = section._repr_html_()
        assert "No distributions" in html

    def test_repr_html_frequencies_empty_skip(self) -> None:
        """Lista vazia de frequências é ignorada sem quebrar (linha 92)."""
        section = DistributionSection(
            histograms={},
            frequencies={"cat": []},
            temporal_charts={},
        )
        html = section._repr_html_()
        assert "No distributions" in html

    def test_repr_html_temporal_empty_skip(self) -> None:
        """Lista vazia de temporais é ignorada sem quebrar (linha 114)."""
        section = DistributionSection(
            histograms={},
            frequencies={},
            temporal_charts={"dt": []},
        )
        html = section._repr_html_()
        assert "No distributions" in html

    def test_str_with_all_types(self) -> None:
        section = DistributionSection(
            histograms={"valor": [HistogramBin(0.0, 10.0, 50)]},
            frequencies={"cat": [FrequencyEntry("A", 40)]},
            temporal_charts={"dt": [TemporalPoint("2024-01", 100)]},
        )
        result = str(section)
        assert "Distributions" in result
        assert "histogram" in result
        assert "frequencies" in result
        assert "temporal" in result

    def test_str_empty_bins_skipped(self) -> None:
        section = DistributionSection(
            histograms={"vazia": []},
            frequencies={},
            temporal_charts={},
        )
        result = str(section)
        assert result == "Distributions\n" + "-" * 40

    def test_str_frequencies_empty_list_skips(self) -> None:
        """Lista vazia de frequências em __str__ é ignorada (linha 159)."""
        section = DistributionSection(
            histograms={},
            frequencies={"cat": []},
            temporal_charts={},
        )
        result = str(section)
        assert "cat" not in result
        assert result == "Distributions\n" + "-" * 40

    def test_str_temporal_empty_list_skips(self) -> None:
        """Lista vazia de temporais em __str__ é ignorada (linha 171)."""
        section = DistributionSection(
            histograms={},
            frequencies={},
            temporal_charts={"dt": []},
        )
        result = str(section)
        assert "dt" not in result

    def test_truncate_text(self) -> None:
        assert _truncate_text("abc", 3) == "abc"
        assert _truncate_text("abcdef", 3) == "..."

    def test_histogram_bin_repr(self) -> None:
        b = HistogramBin(0.0, 10.0, 50)
        r = repr(b)
        assert "HistogramBin" in r

    def test_histogram_bin_str(self) -> None:
        b = HistogramBin(0.0, 10.0, 50)
        s = str(b)
        assert "HistogramBin" in s or "0.0" in s

    def test_frequency_entry_repr(self) -> None:
        e = FrequencyEntry("A", 40)
        r = repr(e)
        assert "FrequencyEntry" in r

    def test_temporal_point_repr(self) -> None:
        p = TemporalPoint("2024-01", 100)
        r = repr(p)
        assert "TemporalPoint" in r


# =========================================================================
# OUTLIER
# =========================================================================

class TestOutlierSection:
    def test_outlier_severity_branches(self) -> None:
        assert _outlier_severity(0.15) == "critical"
        assert _outlier_severity(0.07) == "high"
        assert _outlier_severity(0.03) == "medium"
        assert _outlier_severity(0.005) == "low"

    def test_severity_color_branches(self) -> None:
        assert out_severity_color("critical") == "#dc2626"
        assert out_severity_color("high") == "#d97706"
        assert out_severity_color("medium") == "#eab308"
        assert out_severity_color("low") == "#22c55e"
        assert out_severity_color("unknown") == "#64748b"

    def test_severity_emoji_branches(self) -> None:
        assert _severity_emoji("critical") == "!!"
        assert _severity_emoji("high") == "! "
        assert _severity_emoji("medium") == "- "
        assert _severity_emoji("low") == "  "
        assert _severity_emoji("unknown") == "? "

    def test_repr_html(self) -> None:
        section = OutlierSection(outliers=[
            OutlierSummary("preco", "iqr", 15, 0.15, 10.0, 90.0),
            OutlierSummary("idade", "zscore", 3, 0.03, None, None),
        ])
        html = section._repr_html_()
        assert "preco" in html
        assert "idade" in html
        assert "iqr" in html
        assert "IQR" in html or "iqr" in html

    def test_repr_html_empty(self) -> None:
        section = OutlierSection(outliers=[])
        html = section._repr_html_()
        assert "No outliers" in html

    def test_str(self) -> None:
        section = OutlierSection(outliers=[
            OutlierSummary("preco", "iqr", 15, 0.15, 10.0, 90.0),
            OutlierSummary("idade", "zscore", 3, 0.03, None, None),
        ])
        result = str(section)
        assert "preco" in result
        assert "Outliers" in result

    def test_str_empty(self) -> None:
        section = OutlierSection(outliers=[])
        result = str(section)
        assert "No outliers" in result

    def test_outlier_summary_repr(self) -> None:
        s = OutlierSummary("preco", "iqr", 15, 0.15, 10.0, 90.0)
        r = repr(s)
        assert "OutlierSummary" in r


# =========================================================================
# INSIGHTS
# =========================================================================

class TestInsightsSection:
    def test_severity_helpers(self) -> None:
        assert ins_severity_color("critical") == "#dc2626"
        assert ins_severity_color("high") == "#d97706"
        assert ins_severity_color("medium") == "#eab308"
        assert ins_severity_color("low") == "#22c55e"
        assert ins_severity_color("unknown") == "#64748b"
        assert _severity_icon("critical") == "\u26a0\ufe0f"
        assert _severity_icon("high") == "\u26a0\ufe0f"
        assert _severity_icon("medium") == "\u2139\ufe0f"
        assert _severity_icon("low") == "\u2139\ufe0f"
        assert _severity_marker("critical") == "!!!"
        assert _severity_marker("high") == "!!"
        assert _severity_marker("medium") == "!"
        assert _severity_marker("low") == "i"
        assert _severity_marker("unknown") == "?"

    def test_repr_html(self) -> None:
        section = InsightsSection(insights=[
            InsightDTO("NULLS", "high", "col_a", "Muitos nulos", 0.4),
            InsightDTO("SKEWNESS", "low", "col_b", "Assimetria leve", 1.2),
        ])
        html = section._repr_html_()
        assert "NULLS" in html
        assert "col_a" in html
        assert "col_b" in html

    def test_repr_html_empty(self) -> None:
        """Nenhum insight → mensagem (linha 71)."""
        section = InsightsSection(insights=[])
        html = section._repr_html_()
        assert "No insights" in html

    def test_str(self) -> None:
        section = InsightsSection(insights=[
            InsightDTO("NULLS", "high", "col_a", "Muitos nulos", 0.4),
        ])
        result = str(section)
        assert "Insights" in result
        assert "NULLS" in result

    def test_str_empty(self) -> None:
        """Nenhum insight no __str__ (linha 104)."""
        section = InsightsSection(insights=[])
        result = str(section)
        assert "No insights" in result

    def test_insight_dto_repr(self) -> None:
        dto = InsightDTO("NULLS", "high", "col_a", "Muitos nulos", 0.4)
        r = repr(dto)
        assert "InsightDTO" in r


# =========================================================================
# RECOMMENDATIONS
# =========================================================================

class TestRecommendationsSection:
    def test_priority_helpers(self) -> None:
        assert _priority_color(1) == "#dc2626"
        assert _priority_color(2) == "#d97706"
        assert _priority_color(3) == "#eab308"
        assert _priority_color(4) == "#22c55e"
        assert _priority_color(5) == "#64748b"
        assert _priority_label(1) == "Critical"
        assert _priority_label(2) == "High"
        assert _priority_label(3) == "Medium"
        assert _priority_label(4) == "Low"
        assert _priority_label(5) == "Informational"
        assert _priority_marker(1) == "!!!"
        assert _priority_marker(2) == "!!"
        assert _priority_marker(3) == "! "
        assert _priority_marker(4) == "  "

    def test_repr_html(self) -> None:
        section = RecommendationsSection(recommendations=[
            RecommendationDTO("NULLS", 1, "col_a", "Muitos nulos", "Preencher valores"),
            RecommendationDTO("OUTLIERS", 3, None, "Outliers detectados", "Revisar dados"),
        ])
        html = section._repr_html_()
        assert "P1" in html
        assert "col_a" in html
        assert "OUTLIERS" in html

    def test_repr_html_empty(self) -> None:
        """Nenhuma recomendação → mensagem (linha 76)."""
        section = RecommendationsSection(recommendations=[])
        html = section._repr_html_()
        assert "No recommendations" in html

    def test_str(self) -> None:
        section = RecommendationsSection(recommendations=[
            RecommendationDTO("NULLS", 1, "col_a", "Preencher", "Ação X"),
            RecommendationDTO("OUTLIERS", 3, None, "Outliers", "Ação Y"),
        ])
        result = str(section)
        assert "Recommendations" in result
        assert "P1" in result
        assert "col_a" in result

    def test_str_empty(self) -> None:
        """Nenhuma recomendação no __str__ (linha 107)."""
        section = RecommendationsSection(recommendations=[])
        result = str(section)
        assert "No recommendations" in result

    def test_recommendation_dto_repr(self) -> None:
        dto = RecommendationDTO("NULLS", 1, "col_a", "Preencher", "Ação")
        r = repr(dto)
        assert "RecommendationDTO" in r