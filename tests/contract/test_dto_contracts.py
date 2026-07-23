from __future__ import annotations

"""Testes de contrato para os DTOs da camada de aplicação.

Verifica que todos os dataclasses do módulo ``dto``:
- Podem ser instanciados com os campos obrigatórios
- São frozen (FrozenInstanceError ao alterar atributo após criação)
- Aceitam objetos DTO aninhados quando aplicável
"""

from dataclasses import FrozenInstanceError

import pytest

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


class TestOverviewSectionContract:
    """Contrato do DTO OverviewSection."""

    def test_create_with_all_fields(self) -> None:
        dto: OverviewSection = OverviewSection(
            row_count=1000,
            column_count=15,
            duplicate_count=10,
            duplicate_ratio=0.01,
            missing_ratio=0.02,
            size_estimate=20480,
        )
        assert dto.row_count == 1000
        assert dto.column_count == 15
        assert dto.duplicate_count == 10
        assert dto.duplicate_ratio == 0.01
        assert dto.missing_ratio == 0.02
        assert dto.size_estimate == 20480

    def test_is_frozen(self) -> None:
        dto: OverviewSection = OverviewSection(
            row_count=1,
            column_count=1,
            duplicate_count=0,
            duplicate_ratio=0.0,
            missing_ratio=0.0,
            size_estimate=0,
        )
        with pytest.raises(FrozenInstanceError):
            dto.row_count = 999


class TestSchemaSectionContract:
    """Contrato dos DTOs SchemaColumn e SchemaSection."""

    def test_create_schema_column_with_all_fields(self) -> None:
        col: SchemaColumn = SchemaColumn(
            name="idade",
            type="integer",
            nullable=True,
            inferred_type="numeric",
            null_count=5,
        )
        assert col.name == "idade"
        assert col.type == "integer"
        assert col.nullable is True
        assert col.inferred_type == "numeric"
        assert col.null_count == 5

    def test_create_schema_column_with_none_inferred_type(self) -> None:
        col: SchemaColumn = SchemaColumn(
            name="nome",
            type="string",
            nullable=False,
            inferred_type=None,
            null_count=0,
        )
        assert col.inferred_type is None

    def test_create_schema_section_with_columns(self) -> None:
        cols: list[SchemaColumn] = [
            SchemaColumn("id", "integer", False, None, 0),
            SchemaColumn("nome", "string", True, "text", 5),
        ]
        section: SchemaSection = SchemaSection(columns=cols)
        assert len(section.columns) == 2
        assert section.columns[0].name == "id"
        assert section.columns[1].name == "nome"

    def test_is_frozen(self) -> None:
        col: SchemaColumn = SchemaColumn("c", "int", False, None, 0)
        with pytest.raises(FrozenInstanceError):
            col.name = "x"


class TestStatsSectionContract:
    """Contrato dos DTOs de estatísticas."""

    def test_create_numeric_stats_dto(self) -> None:
        dto: NumericStatsDTO = NumericStatsDTO(
            column_name="receita",
            mean=1500.0,
            std=300.5,
            min=100.0,
            q25=800.0,
            q50=1400.0,
            q75=2000.0,
            max=5000.0,
            skewness=0.5,
            kurtosis=0.2,
        )
        assert dto.column_name == "receita"
        assert dto.mean == 1500.0
        assert dto.kurtosis == 0.2

    def test_create_categorical_stats_dto(self) -> None:
        dto: CategoricalStatsDTO = CategoricalStatsDTO(
            column_name="cidade",
            cardinality=50,
            mode="São Paulo",
            unique_ratio=0.05,
            top_values=[("São Paulo", 300), ("Rio", 200)],
        )
        assert dto.column_name == "cidade"
        assert dto.mode == "São Paulo"
        assert dto.top_values == [("São Paulo", 300), ("Rio", 200)]

    def test_create_temporal_stats_dto(self) -> None:
        dto: TemporalStatsDTO = TemporalStatsDTO(
            column_name="data_venda",
            min_date="2024-01-01",
            max_date="2024-12-31",
            range_days=365,
            gap_count=0,
        )
        assert dto.min_date == "2024-01-01"
        assert dto.range_days == 365

    def test_create_text_stats_dto(self) -> None:
        dto: TextStatsDTO = TextStatsDTO(
            column_name="descricao",
            min_length=10,
            max_length=500,
            avg_length=120.5,
            empty_ratio=0.01,
        )
        assert dto.avg_length == 120.5
        assert dto.empty_ratio == 0.01

    def test_create_boolean_stats_dto(self) -> None:
        dto: BooleanStatsDTO = BooleanStatsDTO(
            column_name="ativo",
            true_count=800,
            false_count=200,
            true_ratio=0.8,
        )
        assert dto.true_count == 800
        assert dto.false_count == 200
        assert dto.true_ratio == 0.8

    def test_create_stats_section_with_empty_dicts(self) -> None:
        section: StatsSection = StatsSection(
            numeric=[],
            categorical=[],
            temporal=[],
            text=[],
            boolean=[],
        )
        assert section.numeric == []
        assert section.boolean == []

    def test_create_stats_section_with_data(self) -> None:
        num: NumericStatsDTO = NumericStatsDTO(
            "v1", 10.0, 2.0, 1.0, 5.0, 10.0, 15.0, 20.0, 0.0, 0.0,
        )
        cat: CategoricalStatsDTO = CategoricalStatsDTO(
            "cat1", 3, "x", 0.3, [("x", 10), ("y", 5)],
        )
        section: StatsSection = StatsSection(
            numeric=[num],
            categorical=[cat],
            temporal=[],
            text=[],
            boolean=[],
        )
        assert len(section.numeric) == 1
        assert len(section.categorical) == 1

    def test_numeric_stats_is_frozen(self) -> None:
        dto: NumericStatsDTO = NumericStatsDTO(
            "c", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        )
        with pytest.raises(FrozenInstanceError):
            dto.column_name = "x"


class TestCorrelationSectionContract:
    """Contrato dos DTOs de correlação."""

    def test_create_correlation_entry(self) -> None:
        entry: CorrelationEntry = CorrelationEntry(
            column_a="idade",
            column_b="receita",
            method="pearson",
            value=0.85,
        )
        assert entry.column_a == "idade"
        assert entry.column_b == "receita"
        assert entry.value == 0.85

    def test_create_correlation_section(self) -> None:
        entries: list[CorrelationEntry] = [
            CorrelationEntry("a", "b", "pearson", 0.8),
        ]
        matrix: dict[str, dict[str, float]] = {
            "a": {"a": 1.0, "b": 0.8},
            "b": {"a": 0.8, "b": 1.0},
        }
        section: CorrelationSection = CorrelationSection(
            correlations=entries,
            matrix=matrix,
            method="pearson",
        )
        assert len(section.correlations) == 1
        assert section.method == "pearson"

    def test_is_frozen(self) -> None:
        entry: CorrelationEntry = CorrelationEntry("a", "b", "pearson", 0.5)
        with pytest.raises(FrozenInstanceError):
            entry.value = 0.9


class TestDistributionSectionContract:
    """Contrato dos DTOs de distribuição."""

    def test_create_histogram_bin(self) -> None:
        bin_: HistogramBin = HistogramBin(lower=0.0, upper=10.0, count=50)
        assert bin_.lower == 0.0
        assert bin_.upper == 10.0
        assert bin_.count == 50

    def test_create_frequency_entry(self) -> None:
        entry: FrequencyEntry = FrequencyEntry(label="A", count=100)
        assert entry.label == "A"
        assert entry.count == 100

    def test_create_temporal_point(self) -> None:
        point: TemporalPoint = TemporalPoint(period="2024-01", count=75)
        assert point.period == "2024-01"
        assert point.count == 75

    def test_create_distribution_section(self) -> None:
        section: DistributionSection = DistributionSection(
            histograms={"nota": [HistogramBin(0, 5, 10)]},
            frequencies={"status": [FrequencyEntry("ok", 200)]},
            temporal_charts={"data": [TemporalPoint("2024-01", 30)]},
        )
        assert "nota" in section.histograms
        assert "status" in section.frequencies
        assert "data" in section.temporal_charts

    def test_is_frozen(self) -> None:
        bin_: HistogramBin = HistogramBin(0.0, 1.0, 1)
        with pytest.raises(FrozenInstanceError):
            bin_.count = 999


class TestOutlierSectionContract:
    """Contrato dos DTOs de outliers."""

    def test_create_outlier_summary(self) -> None:
        summary: OutlierSummary = OutlierSummary(
            column_name="receita",
            method="iqr",
            count=15,
            ratio=0.03,
            bounds_lower=-100.0,
            bounds_upper=5000.0,
        )
        assert summary.column_name == "receita"
        assert summary.count == 15
        assert summary.bounds_lower == -100.0
        assert summary.bounds_upper == 5000.0

    def test_create_outlier_summary_with_none_bounds(self) -> None:
        summary: OutlierSummary = OutlierSummary(
            column_name="categoria",
            method="zscore",
            count=0,
            ratio=0.0,
            bounds_lower=None,
            bounds_upper=None,
        )
        assert summary.bounds_lower is None
        assert summary.bounds_upper is None

    def test_create_outlier_section(self) -> None:
        section: OutlierSection = OutlierSection(
            outliers=[
                OutlierSummary("v1", "iqr", 5, 0.01, -10.0, 100.0),
            ],
        )
        assert len(section.outliers) == 1

    def test_is_frozen(self) -> None:
        s: OutlierSummary = OutlierSummary("c", "m", 0, 0.0, None, None)
        with pytest.raises(FrozenInstanceError):
            s.count = 1


class TestInsightsSectionContract:
    """Contrato dos DTOs de insights."""

    def test_create_insight_dto(self) -> None:
        insight: InsightDTO = InsightDTO(
            category="completude",
            severity="high",
            column="nome",
            message="Coluna nome possui 10% de nulos",
            metric_value=0.1,
        )
        assert insight.category == "completude"
        assert insight.severity == "high"
        assert insight.column == "nome"
        assert insight.metric_value == 0.1

    def test_create_insight_with_none_fields(self) -> None:
        insight: InsightDTO = InsightDTO(
            category="global",
            severity="info",
            column=None,
            message="Dataset possui boa qualidade",
            metric_value=None,
        )
        assert insight.column is None
        assert insight.metric_value is None

    def test_create_insights_section(self) -> None:
        section: InsightsSection = InsightsSection(
            insights=[
                InsightDTO("completude", "high", "x", "Nulos detectados", 0.2),
            ],
        )
        assert len(section.insights) == 1

    def test_is_frozen(self) -> None:
        dto: InsightDTO = InsightDTO("cat", "low", None, "msg", None)
        with pytest.raises(FrozenInstanceError):
            dto.category = "outro"


class TestRecommendationsSectionContract:
    """Contrato dos DTOs de recomendações."""

    def test_create_recommendation_dto(self) -> None:
        rec: RecommendationDTO = RecommendationDTO(
            category="qualidade",
            priority=1,
            column="email",
            message="Email possui formato inconsistente",
            action="Aplicar validação de email",
        )
        assert rec.category == "qualidade"
        assert rec.priority == 1
        assert rec.column == "email"
        assert rec.action == "Aplicar validação de email"

    def test_create_recommendation_with_none_column(self) -> None:
        rec: RecommendationDTO = RecommendationDTO(
            category="performance",
            priority=5,
            column=None,
            message="Dataset pequeno",
            action="Nenhuma ação necessária",
        )
        assert rec.column is None

    def test_create_recommendations_section(self) -> None:
        section: RecommendationsSection = RecommendationsSection(
            recommendations=[
                RecommendationDTO("qualidade", 1, "x", "msg", "ação"),
            ],
        )
        assert len(section.recommendations) == 1

    def test_is_frozen(self) -> None:
        dto: RecommendationDTO = RecommendationDTO("cat", 1, None, "m", "a")
        with pytest.raises(FrozenInstanceError):
            dto.priority = 5


class TestQualitySectionContract:
    """Contrato dos DTOs de qualidade."""

    def test_create_quality_factor_report(self) -> None:
        factor: QualityFactorReport = QualityFactorReport(
            name="Completude",
            score=0.85,
            reason="10% de nulos na coluna email",
            severity="medium",
            affected_columns=["email"],
        )
        assert factor.name == "Completude"
        assert factor.score == 0.85
        assert factor.severity == "medium"
        assert factor.affected_columns == ["email"]

    def test_create_quality_dimension_report(self) -> None:
        factors: list[QualityFactorReport] = [
            QualityFactorReport("Completude", 0.85, "Razão", "medium", ["email"]),
        ]
        dimension: QualityDimensionReport = QualityDimensionReport(
            name="Integridade",
            score=85.0,
            weight=0.3,
            factors=factors,
        )
        assert dimension.name == "Integridade"
        assert dimension.score == 85.0
        assert dimension.weight == 0.3
        assert len(dimension.factors) == 1

    def test_create_quality_report(self) -> None:
        dim: QualityDimensionReport = QualityDimensionReport(
            name="Integridade",
            score=85.0,
            weight=0.3,
            factors=[
                QualityFactorReport("C", 0.9, "OK", "low", []),
            ],
        )
        pen: QualityFactorReport = QualityFactorReport(
            "Nulos", 0.5, "Muitos nulos", "high", ["x"],
        )
        report: QualityReport = QualityReport(
            overall=80.0,
            dimensions=[dim],
            top_penalizers=[pen],
        )
        assert report.overall == 80.0
        assert len(report.dimensions) == 1
        assert len(report.top_penalizers) == 1

    def test_is_frozen(self) -> None:
        f: QualityFactorReport = QualityFactorReport("n", 1.0, "r", "low", [])
        with pytest.raises(FrozenInstanceError):
            f.score = 0.5


class TestEDAReportContract:
    """Contrato de integração do DTO EDAReport."""

    def test_create_full_eda_report(self) -> None:
        overview: OverviewSection = OverviewSection(
            row_count=1000,
            column_count=10,
            duplicate_count=0,
            duplicate_ratio=0.0,
            missing_ratio=0.01,
            size_estimate=40960,
        )
        schema: SchemaSection = SchemaSection(
            columns=[SchemaColumn("id", "integer", False, None, 0)],
        )
        quality: QualityReport = QualityReport(
            overall=90.0,
            dimensions=[],
            top_penalizers=[],
        )
        stats: StatsSection = StatsSection(
            numeric=[],
            categorical=[],
            temporal=[],
            text=[],
            boolean=[],
        )
        distributions: DistributionSection = DistributionSection(
            histograms={},
            frequencies={},
            temporal_charts={},
        )
        correlations: CorrelationSection = CorrelationSection(
            correlations=[],
            matrix={},
            method="pearson",
        )
        outliers: OutlierSection = OutlierSection(outliers=[])
        insights: InsightsSection = InsightsSection(insights=[])
        recommendations: RecommendationsSection = RecommendationsSection(recommendations=[])

        report: EDAReport = EDAReport(
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

        assert report.overview.row_count == 1000
        assert report.schema is schema
        assert report.quality.overall == 90.0
        assert report.stats is stats
        assert report.distributions is distributions
        assert report.correlations.method == "pearson"
        assert report.outliers is outliers
        assert report.insights is insights
        assert report.recommendations is recommendations

    def test_is_frozen(self) -> None:
        s: SchemaSection = SchemaSection(columns=[])
        with pytest.raises(FrozenInstanceError):
            s.columns = [SchemaColumn("x", "int", False, None, 0)]
