from __future__ import annotations

"""Testes para o construtor de prompts do OmniRoute.

Testa PromptBuilder.build: geração de prompt com todas as seções,
dados vazios, coluna única, todos nulos e persona do system prompt.
"""

from dataclasses import replace

from spark_eda.adapters.omniroute.prompt_builder import PromptBuilder
from spark_eda.application.dto.correlation_section import CorrelationEntry, CorrelationSection
from spark_eda.application.dto.distribution_section import DistributionSection
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.insights_section import InsightDTO, InsightsSection
from spark_eda.application.dto.outlier_section import OutlierSection
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.quality_section import QualityDimensionReport, QualityFactorReport, QualityReport
from spark_eda.application.dto.recommendations_section import RecommendationDTO, RecommendationsSection
from spark_eda.application.dto.schema_section import SchemaColumn, SchemaSection
from spark_eda.application.dto.stats_section import (
    BooleanStatsDTO,
    CategoricalStatsDTO,
    NumericStatsDTO,
    StatsSection,
    TemporalStatsDTO,
    TextStatsDTO,
)


def _build_full_report() -> EDAReport:
    """Constrói um EDAReport completo com todas as 9 seções populadas."""
    overview = OverviewSection(
        row_count=1000,
        column_count=5,
        duplicate_count=10,
        duplicate_ratio=0.01,
        missing_ratio=0.05,
        size_estimate=50000,
    )
    schema = SchemaSection(
        columns=[
            SchemaColumn(name="id", type="integer", nullable=False, inferred_type=None, null_count=0),
            SchemaColumn(name="nome", type="string", nullable=True, inferred_type=None, null_count=50),
            SchemaColumn(name="valor", type="double", nullable=True, inferred_type="float", null_count=30),
            SchemaColumn(name="data", type="date", nullable=True, inferred_type=None, null_count=100),
            SchemaColumn(name="ativo", type="boolean", nullable=False, inferred_type=None, null_count=0),
        ],
    )
    quality = QualityReport(
        overall=85.0,
        dimensions=[
            QualityDimensionReport(
                name="completude",
                score=95.0,
                weight=0.3,
                factors=[
                    QualityFactorReport(
                        name="Proporção de nulos",
                        score=0.95,
                        reason="5% de nulos",
                        severity="low",
                        affected_columns=["nome"],
                    ),
                ],
            ),
        ],
        top_penalizers=[
            QualityFactorReport(
                name="Proporção de nulos",
                score=0.95,
                reason="5% de nulos",
                severity="low",
                affected_columns=["nome"],
            ),
        ],
    )
    stats = StatsSection(
        numeric=[
            NumericStatsDTO(
                column_name="valor",
                mean=50.5,
                std=25.2,
                min=0.0,
                q25=25.0,
                q50=50.0,
                q75=75.0,
                max=100.0,
                skewness=0.1,
                kurtosis=-0.5,
            ),
        ],
        categorical=[
            CategoricalStatsDTO(
                column_name="nome",
                cardinality=950,
                mode="item_0000",
                unique_ratio=0.95,
                top_values=[("item_0000", 5), ("item_0001", 4)],
            ),
        ],
        temporal=[
            TemporalStatsDTO(
                column_name="data",
                min_date="2024-01-01",
                max_date="2024-12-31",
                range_days=365,
                gap_count=2,
            ),
        ],
        text=[],
        boolean=[
            BooleanStatsDTO(
                column_name="ativo",
                true_count=600,
                false_count=400,
                true_ratio=0.6,
            ),
        ],
    )
    distributions = DistributionSection(
        histograms={
            "valor": [
                type("HistogramBin", (), {"lower": 0.0, "upper": 50.0, "count": 600})(),
                type("HistogramBin", (), {"lower": 50.0, "upper": 100.0, "count": 400})(),
            ],
        },
        frequencies={
            "nome": [
                type("FrequencyEntry", (), {"label": "item_0000", "count": 5})(),
            ],
        },
        temporal_charts={},
    )
    correlations = CorrelationSection(
        correlations=[
            CorrelationEntry(column_a="id", column_b="valor", method="pearson", value=0.15),
        ],
        matrix={"id": {"id": 1.0, "valor": 0.15}, "valor": {"id": 0.15, "valor": 1.0}},
        method="pearson",
    )
    outliers = OutlierSection(
        outliers=[
            type(
                "OutlierSummary",
                (),
                {
                    "column_name": "valor",
                    "method": "iqr",
                    "count": 5,
                    "ratio": 0.005,
                    "bounds_lower": -10.0,
                    "bounds_upper": 110.0,
                },
            )(),
        ],
    )
    insights = InsightsSection(
        insights=[
            InsightDTO(
                category="nulls",
                severity="low",
                column="nome",
                message="Coluna possui 5% de nulos",
                metric_value=0.05,
            ),
        ],
    )
    recommendations = RecommendationsSection(
        recommendations=[
            RecommendationDTO(
                category="null_treatment",
                priority=3,
                column="nome",
                message="Valores nulos encontrados",
                action="Considere imputação",
            ),
        ],
    )
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


def _build_empty_report() -> EDAReport:
    """Constrói um EDAReport com dataset vazio (0 linhas)."""
    overview = OverviewSection(
        row_count=0,
        column_count=0,
        duplicate_count=0,
        duplicate_ratio=0.0,
        missing_ratio=0.0,
        size_estimate=0,
    )
    schema = SchemaSection(columns=[])
    quality = QualityReport(overall=100.0, dimensions=[], top_penalizers=[])
    stats = StatsSection(numeric=[], categorical=[], temporal=[], text=[], boolean=[])
    distributions = DistributionSection(histograms={}, frequencies={}, temporal_charts={})
    correlations = CorrelationSection(correlations=[], matrix={}, method="pearson")
    outliers = OutlierSection(outliers=[])
    insights = InsightsSection(insights=[])
    recommendations = RecommendationsSection(recommendations=[])
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


def _build_single_column_report() -> EDAReport:
    """Constrói um EDAReport com uma única coluna."""
    overview = OverviewSection(
        row_count=100,
        column_count=1,
        duplicate_count=0,
        duplicate_ratio=0.0,
        missing_ratio=0.0,
        size_estimate=800,
    )
    schema = SchemaSection(
        columns=[
            SchemaColumn(name="id", type="integer", nullable=False, inferred_type=None, null_count=0),
        ],
    )
    quality = QualityReport(overall=100.0, dimensions=[], top_penalizers=[])
    stats = StatsSection(
        numeric=[
            NumericStatsDTO(
                column_name="id",
                mean=50.0,
                std=29.0,
                min=1.0,
                q25=25.0,
                q50=50.0,
                q75=75.0,
                max=100.0,
                skewness=0.0,
                kurtosis=-1.2,
            ),
        ],
        categorical=[],
        temporal=[],
        text=[],
        boolean=[],
    )
    distributions = DistributionSection(histograms={}, frequencies={}, temporal_charts={})
    correlations = CorrelationSection(correlations=[], matrix={}, method="pearson")
    outliers = OutlierSection(outliers=[])
    insights = InsightsSection(insights=[])
    recommendations = RecommendationsSection(recommendations=[])
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


def _build_all_null_report() -> EDAReport:
    """Constrói um EDAReport onde todas as colunas são totalmente nulas."""
    overview = OverviewSection(
        row_count=10,
        column_count=2,
        duplicate_count=0,
        duplicate_ratio=0.0,
        missing_ratio=1.0,
        size_estimate=100,
    )
    schema = SchemaSection(
        columns=[
            SchemaColumn(name="col_a", type="string", nullable=True, inferred_type=None, null_count=10),
            SchemaColumn(name="col_b", type="double", nullable=True, inferred_type=None, null_count=10),
        ],
    )
    quality = QualityReport(overall=0.0, dimensions=[], top_penalizers=[])
    stats = StatsSection(numeric=[], categorical=[], temporal=[], text=[], boolean=[])
    distributions = DistributionSection(histograms={}, frequencies={}, temporal_charts={})
    correlations = CorrelationSection(correlations=[], matrix={}, method="pearson")
    outliers = OutlierSection(outliers=[])
    insights = InsightsSection(insights=[])
    recommendations = RecommendationsSection(recommendations=[])
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


class TestPromptBuilder:
    """Testes para PromptBuilder.build."""

    def test_build_with_all_sections_returns_non_empty_string(self) -> None:
        """build com todas as 9 seções deve retornar string
        não vazia contendo dados das seções."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_contains_dataset_overview_data(self) -> None:
        """O prompt deve conter os dados da seção Overview."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Dataset Overview" in prompt
        assert "1000" in prompt  # row_count
        assert "5" in prompt  # column_count

    def test_build_contains_schema_data(self) -> None:
        """O prompt deve conter os dados da seção Schema."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Schema" in prompt
        assert "id" in prompt
        assert "nome" in prompt
        assert "valor" in prompt
        assert "integer" in prompt
        assert "string" in prompt

    def test_build_contains_quality_data(self) -> None:
        """O prompt deve conter os dados da seção Quality."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Data Quality" in prompt
        assert "85.0" in prompt  # overall score

    def test_build_contains_stats_data(self) -> None:
        """O prompt deve conter os dados da seção Statistics."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Descriptive Statistics" in prompt
        assert "mean=" in prompt
        assert "50.5" in prompt  # mean value
        assert "cardinality" in prompt

    def test_build_contains_correlation_data(self) -> None:
        """O prompt deve conter os dados da seção Correlations."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Correlations" in prompt
        assert "pearson" in prompt

    def test_build_contains_outlier_data(self) -> None:
        """O prompt deve conter os dados da seção Outliers."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Outliers" in prompt
        assert "iqr" in prompt

    def test_build_contains_insights_data(self) -> None:
        """O prompt deve conter os dados da seção Insights."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Insights" in prompt
        assert "nulls" in prompt

    def test_build_contains_recommendations_data(self) -> None:
        """O prompt deve conter os dados da seção Recommendations."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "Recommendations" in prompt
        assert "null_treatment" in prompt

    def test_build_contains_json_instruction(self) -> None:
        """O prompt deve conter a instrução JSON no final."""
        report = _build_full_report()
        prompt = PromptBuilder.build(report)

        assert "executive_analysis" in prompt
        assert "overview" in prompt
        assert "schema" in prompt
        assert "quality" in prompt
        assert "stats" in prompt
        assert "distributions" in prompt
        assert "correlations" in prompt
        assert "outliers" in prompt
        assert "insights" in prompt
        assert "recommendations" in prompt

    def test_build_with_empty_dataset_acknowledges_empty_state(self) -> None:
        """build com dataset vazio (0 linhas) deve reconhecer o
        estado vazio."""
        report = _build_empty_report()
        prompt = PromptBuilder.build(report)

        assert "0" in prompt  # row_count = 0
        assert "Rows" in prompt

    def test_build_with_single_column_handles_limited_structure(self) -> None:
        """build com única coluna deve lidar com estrutura limitada."""
        report = _build_single_column_report()
        prompt = PromptBuilder.build(report)

        assert "id" in prompt
        assert "integer" in prompt
        assert "1" in prompt  # column_count = 1

    def test_build_with_all_null_values_reflects_null_state(self) -> None:
        """build com todos valores nulos deve refletir o estado
        de nulidade."""
        report = _build_all_null_report()
        prompt = PromptBuilder.build(report)

        assert "col_a" in prompt
        assert "col_b" in prompt
        assert "nulls=10" in prompt

    def test_system_prompt_contains_staff_persona(self) -> None:
        """O módulo prompt_builder deve exportar o system prompt
        com persona de staff-level data analyst."""
        # Reimport the module to access _SYSTEM_PROMPT
        from spark_eda.adapters.omniroute import prompt_builder as pb_module

        assert hasattr(pb_module, "_SYSTEM_PROMPT")
        assert "staff-level" in pb_module._SYSTEM_PROMPT
        assert "15+ years" in pb_module._SYSTEM_PROMPT
        assert "data engineer" in pb_module._SYSTEM_PROMPT or "data" in pb_module._SYSTEM_PROMPT.lower()

    # ------------------------------------------------------------------
    # Cobertura de ramos não exercitados
    # ------------------------------------------------------------------

    def test_build_with_text_columns(self) -> None:
        """build com colunas text deve incluir len/avg/empty_ratio."""
        base = _build_full_report()
        text_col = TextStatsDTO(
            column_name="descricao",
            min_length=10,
            max_length=500,
            avg_length=150.0,
            empty_ratio=0.02,
        )
        stats = replace(base.stats, text=[text_col])
        report = replace(base, stats=stats)
        prompt = PromptBuilder.build(report)

        assert "Text columns" in prompt
        assert "descricao" in prompt
        assert "avg=150.0" in prompt
        assert "empty_ratio=2.00%" in prompt

    def test_build_with_temporal_charts(self) -> None:
        """build com temporal_charts nas distribuições deve incluir
        períodos."""
        base = _build_full_report()
        point = type(
            "TemporalPoint",
            (),
            {"period": "2024-01", "count": 100},
        )()
        distributions = replace(base.distributions, temporal_charts={"data": [point, point]})
        report = replace(base, distributions=distributions)
        prompt = PromptBuilder.build(report)

        assert "periods" in prompt
        assert "2024-01" in prompt

    def test_build_with_strong_correlations(self) -> None:
        """build com correlações fortes (|r| >= 0.5) deve listá-las."""
        base = _build_full_report()
        strong = CorrelationEntry(column_a="age", column_b="income", method="pearson", value=0.85)
        weak = CorrelationEntry(column_a="id", column_b="age", method="pearson", value=0.15)
        correlations = CorrelationSection(
            correlations=[strong, weak],
            matrix={"age": {"income": 0.85}, "income": {"age": 0.85}},
            method="pearson",
        )
        report = replace(base, correlations=correlations)
        prompt = PromptBuilder.build(report)

        assert "Strong correlations" in prompt
        assert "age x income" in prompt
        assert "0.8500" in prompt

    def test_build_with_no_strong_correlations(self) -> None:
        """build sem correlações fortes deve mostrar mensagem."""
        base = _build_full_report()
        weak = CorrelationEntry(column_a="id", column_b="age", method="pearson", value=0.15)
        correlations = CorrelationSection(
            correlations=[weak],
            matrix={"id": {"age": 0.15}, "age": {"id": 0.15}},
            method="pearson",
        )
        report = replace(base, correlations=correlations)
        prompt = PromptBuilder.build(report)

        assert "No strong correlations found" in prompt

    def test_build_with_empty_top_values(self) -> None:
        """build com categorical sem top_values deve cobrir
        ramo False de 'if top:'."""
        base = _build_full_report()
        cat_col = type(
            "CategoricalStatsDTO",
            (),
            {
                "column_name": "status",
                "cardinality": 3,
                "mode": "active",
                "unique_ratio": 0.3,
                "top_values": [],
            },
        )()
        stats = replace(base.stats, categorical=[cat_col])
        report = replace(base, stats=stats)
        prompt = PromptBuilder.build(report)

        assert "status" in prompt
        assert "cardinality=3" in prompt
