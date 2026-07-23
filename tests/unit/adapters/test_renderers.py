from __future__ import annotations

"""Testes para os renderizadores de relatório.

Testa HTMLRenderer, TextRenderer e JSONSerializer com EDAReport
e QualityReport mínimos construídos diretamente.
"""

import json
from enum import Enum
from dataclasses import dataclass

import pytest

from spark_eda.adapters.renderers.html_renderer import HTMLRenderer
from spark_eda.adapters.renderers.json_serializer import JSONSerializer, _default_serializer
from spark_eda.adapters.renderers.text_renderer import TextRenderer
from spark_eda.adapters.renderers.text_renderer import (
    _bold, _dim, _red, _green, _yellow, _blue, _cyan, _gray,
)
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


@dataclass(frozen=True)
class _NestedDataclass:
    value: str


@dataclass(frozen=True)
class _Container:
    nested: _NestedDataclass
    tags: set[str]
    kind: object  # will hold an Enum


class _DummyEnum(Enum):
    A = "alpha"
    B = "beta"


def _build_minimal_report() -> EDAReport:
    """Constrói um EDAReport mínimo para testes de renderização."""
    overview: OverviewSection = OverviewSection(
        row_count=100,
        column_count=2,
        duplicate_count=0,
        duplicate_ratio=0.0,
        missing_ratio=0.0,
        size_estimate=8000,
    )
    schema: SchemaSection = SchemaSection(
        columns=[
            SchemaColumn(name="id", type="integer", nullable=False, inferred_type=None, null_count=0),
            SchemaColumn(name="nome", type="string", nullable=True, inferred_type=None, null_count=5),
        ],
    )
    quality: QualityReport = QualityReport(
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
        correlations=[
            CorrelationEntry(column_a="id", column_b="id", method="pearson", value=1.0),
        ],
        matrix={"id": {"id": 1.0}},
        method="pearson",
    )
    outliers: OutlierSection = OutlierSection(outliers=[])
    insights: InsightsSection = InsightsSection(
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
    recommendations: RecommendationsSection = RecommendationsSection(
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


def _build_quality_report(
    overall: float,
    top_penalizers: list[QualityFactorReport] | None = None,
) -> QualityReport:
    """Constrói um QualityReport com um único fator."""
    return QualityReport(
        overall=overall,
        dimensions=[
            QualityDimensionReport(
                name="completude",
                score=overall,
                weight=0.3,
                factors=[
                    QualityFactorReport(
                        name="Nulos",
                        score=overall / 100.0,
                        reason="Motivo",
                        severity="low",
                        affected_columns=[],
                    ),
                ],
            ),
        ],
        top_penalizers=top_penalizers or [],
    )


class TestHTMLRenderer:
    """Testes para o renderizador HTML."""

    def test_render_report_contains_html_structure(self) -> None:
        """O HTML gerado deve conter as tags básicas de documento."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        html: str = HTMLRenderer.render_report(report)

        # Assert
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "spark_eda" in html

    def test_render_report_contains_section_titles(self) -> None:
        """O HTML deve conter os títulos das seções do relatório."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        html: str = HTMLRenderer.render_report(report)

        # Assert
        assert "Overview" in html
        assert "Schema" in html
        assert "Quality" in html
        assert "Outliers" in html
        assert "Insights" in html
        assert "Recommendations" in html

    def test_render_quality_contains_gauge(self) -> None:
        """O fragmento de qualidade deve conter o gauge SVG."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        html: str = HTMLRenderer.render_quality_report(report.quality)

        # Assert
        assert '<svg' in html
        assert 'QUALITY' in html
        assert report.quality.overall is not None

    def test_render_quality_page(self) -> None:
        """render_quality deve gerar uma página HTML completa."""
        # Arrange
        quality: QualityReport = _build_quality_report(95.0)

        # Act
        html: str = HTMLRenderer.render_quality(quality)

        # Assert
        assert "<!DOCTYPE html>" in html
        assert "Data Quality" in html
        assert '<svg' in html

    def test_render_quality_report_low_score_uses_red(self) -> None:
        """render_quality_report com score < 40 deve usar cor
        vermelha (#dc2626).
        """
        # Arrange
        quality: QualityReport = _build_quality_report(30.0)

        # Act
        html: str = HTMLRenderer.render_quality_report(quality)

        # Assert
        assert "#dc2626" in html

    def test_render_quality_report_medium_score_uses_orange(self) -> None:
        """render_quality_report com score entre 40 e 69 deve usar
        cor laranja (#d97706).
        """
        # Arrange
        quality: QualityReport = _build_quality_report(50.0)

        # Act
        html: str = HTMLRenderer.render_quality_report(quality)

        # Assert
        assert "#d97706" in html

    def test_render_quality_report_zero_score(self) -> None:
        """render_quality_report com score 0 deve exibir 0%."""
        # Arrange
        quality: QualityReport = _build_quality_report(0.0)

        # Act
        html: str = HTMLRenderer.render_quality_report(quality)

        # Assert
        assert "0,0" in html or "0.0" in html

    def test_render_quality_report_with_penalizers(self) -> None:
        """render_quality_report com top_penalizers deve incluir
        seção de penalizadores.
        """
        # Arrange
        penalizer: QualityFactorReport = QualityFactorReport(
            name="Cardinalidade",
            score=0.60,
            reason="Alta cardinalidade",
            severity="high",
            affected_columns=["col"],
        )
        quality: QualityReport = _build_quality_report(70.0, top_penalizers=[penalizer])

        # Act
        html: str = HTMLRenderer.render_quality_report(quality)

        # Assert
        assert "Top Penalizers" in html
        assert "Alta cardinalidade" in html

    def test_render_section_with_repr_html(self) -> None:
        """render_section deve chamar _repr_html_ quando disponível."""
        # Arrange
        section: OverviewSection = OverviewSection(
            row_count=10, column_count=1, duplicate_count=0,
            duplicate_ratio=0.0, missing_ratio=0.0, size_estimate=100,
        )

        # Act
        html: str = HTMLRenderer.render_section(section)

        # Assert
        assert "Rows" in html

    def test_render_section_without_repr_html(self) -> None:
        """render_section sem _repr_html_ deve retornar repr()."""
        # Arrange
        obj: object = object()

        # Act
        html: str = HTMLRenderer.render_section(obj)

        # Assert
        assert "<div>" in html
        assert "object" in html


class TestTextRenderer:
    """Testes para o renderizador de texto."""

    def test_render_report_contains_report_header(self) -> None:
        """O texto gerado deve conter o cabeçalho do relatório."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        text: str = TextRenderer.render_report(report)

        # Assert
        assert "spark_eda" in text
        assert "Exploratory Data Analysis Report" in text

    def test_render_report_contains_section_numbers(self) -> None:
        """O texto deve conter os números das seções."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        text: str = TextRenderer.render_report(report)

        # Assert
        assert "1. Overview" in text
        assert "2. Schema" in text
        assert "3. Quality" in text
        assert "4. Statistics" in text

    def test_render_quality_contains_overall_score(self) -> None:
        """O fragmento de qualidade deve exibir o score overall."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        text: str = TextRenderer.render_quality_report(report.quality)

        # Assert
        assert "Quality" in text
        assert "Overall" in text
        assert "Completude" in text

    def test_render_quality_page(self) -> None:
        """render_quality deve gerar página de qualidade formatada."""
        # Arrange
        quality: QualityReport = _build_quality_report(85.0)

        # Act
        text: str = TextRenderer.render_quality(quality)

        # Assert
        assert "Data Quality" in text
        assert "Overall" in text

    def test_render_quality_report_with_penalizers(self) -> None:
        """render_quality_report com top_penalizers deve incluir
        Top Penalizers.
        """
        # Arrange
        penalizer: QualityFactorReport = QualityFactorReport(
            name="Nulos", score=0.50, reason="50% nulos",
            severity="critical", affected_columns=["x"],
        )
        quality: QualityReport = _build_quality_report(50.0, top_penalizers=[penalizer])

        # Act
        text: str = TextRenderer.render_quality_report(quality)

        # Assert
        assert "Top Penalizers" in text
        assert "50% nulos" in text

    def test_render_quality_report_without_penalizers(self) -> None:
        """render_quality_report sem top_penalizers não deve
        incluir seção de penalizadores.
        """
        # Arrange
        quality: QualityReport = _build_quality_report(100.0)

        # Act
        text: str = TextRenderer.render_quality_report(quality)

        # Assert
        assert "Top Penalizers" not in text

    def test_render_section_with_str(self) -> None:
        """render_section deve chamar __str__ quando disponível."""
        # Arrange
        section: OverviewSection = OverviewSection(
            row_count=5, column_count=1, duplicate_count=0,
            duplicate_ratio=0.0, missing_ratio=0.0, size_estimate=50,
        )

        # Act
        result: str = TextRenderer.render_section(section)

        # Assert
        assert "Overview" in result

    def test_render_section_without_str(self) -> None:
        """render_section sem __str__ deve retornar repr()."""
        # Arrange
        class _NoStr:
            """Classe cujo __str__ levanta AttributeError para
            que hasattr retorne False."""
            @property
            def __str__(self) -> str:
                msg = "__str__ not available"
                raise AttributeError(msg)

        obj: _NoStr = _NoStr()

        # Act
        result: str = TextRenderer.render_section(obj)

        # Assert
        assert "_NoStr" in result

    def test_ansi_helpers_return_strings(self) -> None:
        """Funções _bold, _dim, _red, _green, _yellow, _blue,
        _cyan, _gray devem retornar strings.
        """
        assert isinstance(_bold("x"), str)
        assert isinstance(_dim("x"), str)
        assert isinstance(_red("x"), str)
        assert isinstance(_green("x"), str)
        assert isinstance(_yellow("x"), str)
        assert isinstance(_blue("x"), str)
        assert isinstance(_cyan("x"), str)
        assert isinstance(_gray("x"), str)


class TestJSONSerializer:
    """Testes para o serializador JSON."""

    def test_serialize_report_returns_valid_json(self) -> None:
        """A serialização de um EDAReport deve retornar JSON válido."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        json_str: str = JSONSerializer.serialize_report(report)
        data: dict = json.loads(json_str)

        # Assert
        assert isinstance(data, dict)
        assert "overview" in data
        assert "schema" in data
        assert "quality" in data
        assert "stats" in data
        assert "distributions" in data
        assert "correlations" in data
        assert "outliers" in data
        assert "insights" in data
        assert "recommendations" in data

    def test_serialize_report_overview_fields(self) -> None:
        """O JSON deve conter os campos corretos na seção overview."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        json_str: str = JSONSerializer.serialize_report(report)
        data: dict = json.loads(json_str)

        # Assert
        overview: dict = data["overview"]
        assert overview["row_count"] == 100
        assert overview["column_count"] == 2

    def test_serialize_quality_returns_valid_json(self) -> None:
        """A serialização de um QualityReport deve retornar JSON válido."""
        # Arrange
        report: EDAReport = _build_minimal_report()

        # Act
        json_str: str = JSONSerializer.serialize_quality(report.quality)
        data: dict = json.loads(json_str)

        # Assert
        assert isinstance(data, dict)
        assert "overall" in data
        assert "dimensions" in data
        assert "top_penalizers" in data
        assert data["overall"] == 95.0

    def test_default_serializer_dataclass(self) -> None:
        """_default_serializer deve converter dataclass para dict."""
        # Arrange
        obj: _NestedDataclass = _NestedDataclass(value="test")

        # Act
        result: dict = _default_serializer(obj)

        # Assert
        assert result == {"value": "test"}

    def test_default_serializer_set(self) -> None:
        """_default_serializer deve converter set para list."""
        # Arrange & Act
        result: list = _default_serializer({1, 2, 3})

        # Assert
        assert sorted(result) == [1, 2, 3]
        assert isinstance(result, list)

    def test_default_serializer_enum(self) -> None:
        """_default_serializer deve extrair .value de Enum."""
        # Arrange & Act
        result: str = _default_serializer(_DummyEnum.A)

        # Assert
        assert result == "alpha"

    def test_default_serializer_raises_on_unsupported(self) -> None:
        """_default_serializer deve levantar TypeError para tipo
        não suportado.
        """
        # Arrange & Act & Assert
        with pytest.raises(TypeError, match="Non-serializable type"):
            _default_serializer(b"bytes")  # type: ignore[arg-type]

    def test_serialize_report_with_nested_dataclass_uses_default(self) -> None:
        """serialize_report deve usar _default_serializer para
        tipos aninhados não serializáveis diretamente.
        """
        # Arrange
        container: _Container = _Container(
            nested=_NestedDataclass(value="inner"),
            tags={"a", "b"},
            kind=_DummyEnum.B,
        )

        # Act
        json_str: str = JSONSerializer.serialize_report(container)
        data: dict = json.loads(json_str)

        # Assert
        assert data["nested"]["value"] == "inner"
        assert sorted(data["tags"]) == ["a", "b"]
        assert data["kind"] == "beta"
