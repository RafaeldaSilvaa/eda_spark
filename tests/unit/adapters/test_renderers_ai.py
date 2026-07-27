from __future__ import annotations

"""Testes para renderização de comentários AI nos relatórios.

Testa HTMLRenderer, TextRenderer e JSONSerializer com
AiCommentary presente e ausente.
"""

import json

from spark_eda.adapters.omniroute.models import AiCommentary
from spark_eda.adapters.renderers.html_renderer import HTMLRenderer
from spark_eda.adapters.renderers.json_serializer import JSONSerializer
from spark_eda.adapters.renderers.text_renderer import TextRenderer
from spark_eda.application.dto.correlation_section import CorrelationEntry, CorrelationSection
from spark_eda.application.dto.distribution_section import DistributionSection
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.insights_section import InsightDTO, InsightsSection
from spark_eda.application.dto.outlier_section import OutlierSection
from spark_eda.application.dto.overview_section import OverviewSection
from spark_eda.application.dto.quality_section import QualityDimensionReport, QualityFactorReport, QualityReport
from spark_eda.application.dto.recommendations_section import RecommendationDTO, RecommendationsSection
from spark_eda.application.dto.schema_section import SchemaColumn, SchemaSection
from spark_eda.application.dto.stats_section import StatsSection


def _build_base_report() -> EDAReport:
    """Constrói um EDAReport básico sem commentary."""
    overview = OverviewSection(
        row_count=100,
        column_count=2,
        duplicate_count=0,
        duplicate_ratio=0.0,
        missing_ratio=0.05,
        size_estimate=8000,
    )
    schema = SchemaSection(
        columns=[
            SchemaColumn(name="id", type="integer", nullable=False, inferred_type=None, null_count=0),
            SchemaColumn(name="nome", type="string", nullable=True, inferred_type=None, null_count=5),
        ],
    )
    quality = QualityReport(
        overall=95.0,
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
    stats = StatsSection(numeric=[], categorical=[], temporal=[], text=[], boolean=[])
    distributions = DistributionSection(histograms={}, frequencies={}, temporal_charts={})
    correlations = CorrelationSection(
        correlations=[
            CorrelationEntry(column_a="id", column_b="id", method="pearson", value=1.0),
        ],
        matrix={"id": {"id": 1.0}},
        method="pearson",
    )
    outliers = OutlierSection(outliers=[])
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


class TestHTMLRendererAI:
    """Testes para renderização de AI commentary no HTML."""

    def test_commentary_present_shows_ai_block(self) -> None:
        """HTML deve conter bloco AI quando commentary está presente."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="AI overview insight",
            schema="AI schema note",
            quality="AI quality comment",
            stats="AI stats analysis",
            distributions="AI distributions",
            correlations="AI correlation insight",
            outliers="AI outlier detection",
            insights="AI insight",
            recommendations="AI recommendation",
            executive_analysis="Cross-cutting executive analysis text",
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        html = HTMLRenderer.render_report(report)

        assert "[AI-generated suggestion]" in html
        assert "AI overview insight" in html
        assert "AI schema note" in html
        assert "AI quality comment" in html
        assert "AI recommendation" in html

    def test_commentary_present_shows_executive_analysis_section(self) -> None:
        """HTML deve conter seção Executive Analysis quando
        commentary está presente."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="AI overview",
            executive_analysis="Executive analysis text",
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        html = HTMLRenderer.render_report(report)

        assert "Executive Analysis" in html
        assert "Executive analysis text" in html

    def test_commentary_absent_no_ai_sections(self) -> None:
        """HTML sem commentary não deve conter AI sections."""
        report = _build_base_report()
        report = type(report)(**{**report.__dict__, "commentary": None})
        html = HTMLRenderer.render_report(report)

        assert "[AI-generated suggestion]" not in html
        assert "Executive Analysis" not in html
        # Should still contain normal sections
        assert "Overview" in html
        assert "Schema" in html
        assert "Quality" in html

    def test_commentary_absent_identical_to_pre_ai(self) -> None:
        """HTML sem commentary deve ser igual ao formato anterior
        (sem AI)."""
        report = _build_base_report()
        report_no_commentary = type(report)(**{**report.__dict__, "commentary": None})
        html = HTMLRenderer.render_report(report_no_commentary)

        # Verify no AI-related content
        assert "ai-commentary" not in html
        assert "ai_commentary" not in html
        assert "ai commentary" not in html.lower()[:500]

    def test_commentary_with_none_per_section_does_not_show(self) -> None:
        """HTML não deve mostrar AI block para seções com
        commentary None."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="Only overview has AI",
            schema=None,
            quality=None,
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        html = HTMLRenderer.render_report(report)

        assert "Only overview has AI" in html
        assert "[AI-generated suggestion]" in html


class TestTextRendererAI:
    """Testes para renderização de AI commentary no Texto."""

    def test_commentary_present_shows_ai_label(self) -> None:
        """Texto deve conter label AI quando commentary está presente."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="AI overview text",
            schema="AI schema text",
            quality="AI quality text",
            stats="AI stats text",
            distributions="AI distributions text",
            correlations="AI correlations text",
            outliers="AI outliers text",
            insights="AI insights text",
            recommendations="AI recommendations text",
            executive_analysis="Executive summary text",
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        text = TextRenderer.render_report(report)

        assert "[AI-generated suggestion]" in text
        assert "AI overview text" in text
        assert "AI schema text" in text
        assert "AI quality text" in text

    def test_commentary_present_shows_executive_analysis_section(self) -> None:
        """Texto deve conter seção Executive Analysis quando
        commentary está presente."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="AI overview",
            executive_analysis="Executive analysis text",
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        text = TextRenderer.render_report(report)

        assert "Executive Analysis" in text
        assert "Executive analysis text" in text

    def test_commentary_absent_no_ai_sections(self) -> None:
        """Texto sem commentary não deve conter AI sections."""
        report = _build_base_report()
        report = type(report)(**{**report.__dict__, "commentary": None})
        text = TextRenderer.render_report(report)

        assert "[AI-generated suggestion]" not in text
        assert "Executive Analysis" not in text
        # Should still contain normal sections
        assert "1. Overview" in text
        assert "2. Schema" in text

    def test_commentary_with_none_per_section_does_not_show(self) -> None:
        """Texto não deve mostrar AI block para seções com
        commentary None."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="Only overview has AI",
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        text = TextRenderer.render_report(report)

        assert "Only overview has AI" in text
        assert "[AI-generated suggestion]" in text


class TestJSONSerializerAI:
    """Testes para serialização JSON de AI commentary."""

    def test_commentary_present_contains_commentary_key(self) -> None:
        """JSON deve conter chave commentary com todos os campos
        quando AiCommentary está presente."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="json overview",
            schema="json schema",
            quality="json quality",
            stats="json stats",
            distributions="json distributions",
            correlations="json correlations",
            outliers="json outliers",
            insights="json insights",
            recommendations="json recommendations",
            executive_analysis="json executive",
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        json_str = JSONSerializer.serialize_report(report)
        data = json.loads(json_str)

        assert "commentary" in data
        assert data["commentary"]["overview"] == "json overview"
        assert data["commentary"]["schema"] == "json schema"
        assert data["commentary"]["quality"] == "json quality"
        assert data["commentary"]["stats"] == "json stats"
        assert data["commentary"]["distributions"] == "json distributions"
        assert data["commentary"]["correlations"] == "json correlations"
        assert data["commentary"]["outliers"] == "json outliers"
        assert data["commentary"]["insights"] == "json insights"
        assert data["commentary"]["recommendations"] == "json recommendations"
        assert data["commentary"]["executive_analysis"] == "json executive"

    def test_commentary_absent_contains_null_commentary(self) -> None:
        """JSON deve conter commentary como null quando
        AiCommentary está ausente."""
        report = _build_base_report()
        report = type(report)(**{**report.__dict__, "commentary": None})
        json_str = JSONSerializer.serialize_report(report)
        data = json.loads(json_str)

        assert "commentary" in data
        assert data["commentary"] is None

    def test_commentary_present_all_main_sections_still_present(self) -> None:
        """JSON com commentary ainda deve conter todas as seções
        principais."""
        report = _build_base_report()
        commentary = AiCommentary(overview="test")
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        json_str = JSONSerializer.serialize_report(report)
        data = json.loads(json_str)

        assert "overview" in data
        assert "schema" in data
        assert "quality" in data
        assert "stats" in data
        assert "distributions" in data
        assert "correlations" in data
        assert "outliers" in data
        assert "insights" in data
        assert "recommendations" in data

    def test_commentary_absent_no_ai_fields_in_sections(self) -> None:
        """JSON sem commentary não deve conter campos de AI nas
        seções individuais."""
        report = _build_base_report()
        report = type(report)(**{**report.__dict__, "commentary": None})
        json_str = JSONSerializer.serialize_report(report)
        data = json.loads(json_str)

        # Non-commentary fields should still exist
        assert data["overview"]["row_count"] == 100

    def test_commentary_with_partial_fields(self) -> None:
        """JSON deve refletir campos parciais de commentary
        corretamente."""
        report = _build_base_report()
        commentary = AiCommentary(
            overview="Only overview",
            executive_analysis="Executive only",
        )
        report = type(report)(**{**report.__dict__, "commentary": commentary})
        json_str = JSONSerializer.serialize_report(report)
        data = json.loads(json_str)

        assert data["commentary"]["overview"] == "Only overview"
        assert data["commentary"]["executive_analysis"] == "Executive only"
        assert data["commentary"]["schema"] is None
        assert data["commentary"]["quality"] is None
