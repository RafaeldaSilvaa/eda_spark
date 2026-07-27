from __future__ import annotations

"""Testes para os presenters de análise e qualidade.

Testa a conversão de entidades de domínio (DatasetAnalysis, QualityScore)
em DTOs de apresentação (EDAReport, QualityReport).
"""

from datetime import datetime
from unittest import mock

import pytest

from spark_eda.adapters.presenters.analysis_presenter import AnalysisPresenter
from spark_eda.adapters.presenters.quality_presenter import QualityPresenter
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.quality_section import QualityReport
from spark_eda.domain.entities.column_metadata import ColumnMetadata
from spark_eda.domain.entities.column_profile import ColumnProfile
from spark_eda.domain.entities.correlation import Correlation
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.distribution import (
    CategoricalDistribution,
    NumericDistribution,
    TemporalDistribution,
)
from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.outlier import OutlierInfo
from spark_eda.domain.entities.quality_score import QualityDimension, QualityFactor, QualityScore
from spark_eda.domain.entities.recommendation import Recommendation
from spark_eda.domain.entities.statistic import (
    BooleanStats,
    CategoricalStats,
    NumericStats,
    TemporalStats,
    TextStats,
)
from spark_eda.domain.value_objects.correlation_method import CorrelationMethod
from spark_eda.domain.value_objects.data_type import DataType
from spark_eda.domain.value_objects.insight_category import InsightCategory
from spark_eda.domain.value_objects.outlier_method import OutlierMethod
from spark_eda.domain.value_objects.recommendation_category import RecommendationCategory
from spark_eda.domain.value_objects.severity import Severity


class TestAnalysisPresenter:
    """Testes para o presenter de análise completa."""

    def test_present_analysis_returns_eda_report(self) -> None:
        """O método present_analysis deve retornar uma instância de
        EDAReport com todas as seções preenchidas.
        """
        # Arrange
        metadata: ColumnMetadata = ColumnMetadata(
            name="idade",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        stats: NumericStats = NumericStats(
            mean=35.0,
            std=10.0,
            min=18.0,
            q25=25.0,
            q50=33.0,
            q75=42.0,
            max=65.0,
            skewness=0.0,
            kurtosis=-1.0,
        )
        profile: ColumnProfile = ColumnProfile(
            metadata=metadata,
            stats=stats,
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"idade": profile},
        )
        quality: QualityScore = QualityScore(
            overall=100.0,
            dimensions={},
            top_penalizers=[],
        )
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert
        assert isinstance(report, EDAReport)
        assert report.overview.row_count == 100
        assert report.overview.column_count == 1
        assert report.overview.duplicate_count == 0
        assert report.overview.missing_ratio == 0.0
        assert report.quality.overall == 100.0
        assert len(report.schema.columns) == 1
        assert report.schema.columns[0].name == "idade"
        assert report.schema.columns[0].type == "integer"

    def test_present_analysis_creates_all_sections(self) -> None:
        """O EDAReport gerado deve conter todas as 9 seções esperadas."""
        # Arrange
        metadata: ColumnMetadata = ColumnMetadata(
            name="valor",
            data_type=DataType.DOUBLE,
            nullable=True,
            inferred_type=None,
            null_count=5,
            non_null_count=95,
        )
        stats: NumericStats = NumericStats(
            mean=50.0,
            std=15.0,
            min=0.0,
            q25=25.0,
            q50=50.0,
            q75=75.0,
            max=100.0,
            skewness=0.5,
            kurtosis=2.0,
        )
        profile: ColumnProfile = ColumnProfile(
            metadata=metadata,
            stats=stats,
            distribution=None,
            outlier=None,
        )
        data_profile: DataProfile = DataProfile(
            id="full_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={"valor": profile},
        )
        factor: QualityFactor = QualityFactor(
            name="Proporção de nulos",
            score=0.95,
            internal_weight=1.0,
            contribution=0.95,
            reason="5% de valores nulos",
            severity=Severity.LOW,
            affected_columns=["valor"],
        )
        dimension: QualityDimension = QualityDimension(
            name="completude",
            score=95.0,
            weight=0.3,
            contribution=28.5,
            factors=[factor],
        )
        quality: QualityScore = QualityScore(
            overall=95.0,
            dimensions={"completude": dimension},
            top_penalizers=[factor],
        )
        insight: Insight = Insight(
            category=InsightCategory.NULLS,
            severity=Severity.LOW,
            column="valor",
            message="Coluna 'valor' possui 5% de nulos",
            metric_value=0.05,
        )
        recommendation: Recommendation = Recommendation(
            category=RecommendationCategory.NULL_TREATMENT,
            priority=3,
            column="valor",
            message="Valores nulos em 'valor'",
            action="Considere imputar a média",
        )
        correlation: Correlation = Correlation(
            column_a="valor",
            column_b="valor",
            method=CorrelationMethod.PEARSON,
            value=1.0,
        )
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[correlation],
            insights=[insight],
            recommendations=[recommendation],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert
        assert report.overview is not None
        assert report.schema is not None
        assert report.quality is not None
        assert report.stats is not None
        assert report.distributions is not None
        assert report.correlations is not None
        assert report.outliers is not None
        assert report.insights is not None
        assert report.recommendations is not None
        assert report.overview.missing_ratio == 0.05
        assert len(report.insights.insights) == 1
        assert report.insights.insights[0].category == "nulls"
        assert len(report.recommendations.recommendations) == 1
        assert report.correlations.method == "pearson"

    def test_present_quality_delegates_to_quality_presenter(self) -> None:
        """present_quality no AnalysisPresenter deve delegar e
        retornar QualityReport.
        """
        # Arrange
        factor: QualityFactor = QualityFactor(
            name="Nulos",
            score=0.80,
            internal_weight=1.0,
            contribution=0.80,
            reason="20% nulos",
            severity=Severity.HIGH,
            affected_columns=["x"],
        )
        dim: QualityDimension = QualityDimension(
            name="completude",
            score=80.0,
            weight=0.3,
            contribution=24.0,
            factors=[factor],
        )
        quality: QualityScore = QualityScore(
            overall=80.0,
            dimensions={"completude": dim},
            top_penalizers=[factor],
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        result: QualityReport = presenter.present_quality(quality)

        # Assert
        assert isinstance(result, QualityReport)
        assert result.overall == 80.0

    def test_build_overview_with_unicidade_dimension(self) -> None:
        """_build_overview extrai duplicate_count da dimensão
        unicidade quando disponível.
        """
        # Arrange
        factor: QualityFactor = QualityFactor(
            name="Linhas duplicatas",
            score=0.50,
            internal_weight=1.0,
            contribution=0.50,
            reason="Existem 15 registros duplicados (15.0%)",
            severity=Severity.MEDIUM,
            affected_columns=["15"],
        )
        dim: QualityDimension = QualityDimension(
            name="unicidade",
            score=50.0,
            weight=0.2,
            contribution=10.0,
            factors=[factor],
        )
        quality: QualityScore = QualityScore(
            overall=80.0,
            dimensions={"unicidade": dim},
            top_penalizers=[factor],
        )
        metadata: ColumnMetadata = ColumnMetadata(
            name="id",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        data_profile: DataProfile = DataProfile(
            id="dup_test",
            columns=(metadata,),
            row_count=100,
            column_profiles={},
        )
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert — reason contains "15", so duplicate_count = 15
        assert report.overview.duplicate_count == 15

    def test_build_overview_with_unicidade_dimension_fallback_to_affected(self) -> None:
        """_build_overview fallback p/ affected_columns[0] se reason
        não tiver dígitos.
        """
        # Arrange
        factor: QualityFactor = QualityFactor(
            name="Duplicata",
            score=0.50,
            internal_weight=1.0,
            contribution=0.50,
            reason="Muitas duplicatas encontradas",
            severity=Severity.MEDIUM,
            affected_columns=["42"],
        )
        dim: QualityDimension = QualityDimension(
            name="unicidade",
            score=50.0,
            weight=0.2,
            contribution=10.0,
            factors=[factor],
        )
        quality: QualityScore = QualityScore(
            overall=80.0,
            dimensions={"unicidade": dim},
            top_penalizers=[factor],
        )
        metadata: ColumnMetadata = ColumnMetadata(
            name="id",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        data_profile: DataProfile = DataProfile(
            id="dup_fallback",
            columns=(metadata,),
            row_count=100,
            column_profiles={},
        )
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert — fallback para affected_columns[0] = "42"
        assert report.overview.duplicate_count == 42

    def test_build_overview_size_estimate_all_types(self) -> None:
        """_build_overview deve calcular size_estimate para todos os
        DataType branches.
        """
        # Arrange
        cols: list[ColumnMetadata] = [
            ColumnMetadata(
                name="c_dec",
                data_type=DataType.DECIMAL,
                nullable=False,
                inferred_type=None,
                null_count=0,
                non_null_count=10,
            ),
            ColumnMetadata(
                name="c_bool",
                data_type=DataType.BOOLEAN,
                nullable=False,
                inferred_type=None,
                null_count=0,
                non_null_count=10,
            ),
            ColumnMetadata(
                name="c_date",
                data_type=DataType.DATE,
                nullable=False,
                inferred_type=None,
                null_count=0,
                non_null_count=10,
            ),
            ColumnMetadata(
                name="c_ts",
                data_type=DataType.TIMESTAMP,
                nullable=False,
                inferred_type=None,
                null_count=0,
                non_null_count=10,
            ),
            ColumnMetadata(
                name="c_other",
                data_type=DataType.OTHER,
                nullable=False,
                inferred_type=None,
                null_count=0,
                non_null_count=10,
            ),
        ]
        data_profile: DataProfile = DataProfile(
            id="size_test",
            columns=tuple(cols),
            row_count=10,
            column_profiles={},
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert: 10*12 + 10*1 + 10*4 + 10*8 + 10*50 = 120+10+40+80+500 = 750
        assert report.overview.size_estimate == 750

    def test_build_stats_with_none_profile_skips_column(self) -> None:
        """_build_stats deve pular coluna se column_profile for None
        ou stats for None (linha 192).
        """
        # Arrange
        metadata: ColumnMetadata = ColumnMetadata(
            name="skip_me",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="skip_test",
            columns=(metadata,),
            row_count=10,
            column_profiles={
                "skip_me": ColumnProfile(
                    metadata=metadata,
                    stats=None,
                    distribution=None,
                    outlier=None,
                )
            },
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert — stats sections devem estar vazios
        assert len(report.stats.numeric) == 0
        assert len(report.stats.categorical) == 0
        assert len(report.stats.temporal) == 0
        assert len(report.stats.text) == 0
        assert len(report.stats.boolean) == 0

    def test_build_overview_with_unicidade_non_duplicate_factor(self) -> None:
        """_build_overview com fator unicidade sem 'duplicata' no nome (linha 134 else)."""
        factor: QualityFactor = QualityFactor(
            name="Cardinalidade alta",
            score=0.90,
            internal_weight=1.0,
            contribution=0.90,
            reason="Alta cardinalidade detectada",
            severity=Severity.LOW,
            affected_columns=[],
        )
        dim: QualityDimension = QualityDimension(
            name="unicidade",
            score=90.0,
            weight=0.2,
            contribution=18.0,
            factors=[factor],
        )
        quality: QualityScore = QualityScore(overall=90.0, dimensions={"unicidade": dim}, top_penalizers=[factor])
        metadata: ColumnMetadata = ColumnMetadata(
            name="id",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=100,
        )
        data_profile: DataProfile = DataProfile(
            id="non_dup",
            columns=(metadata,),
            row_count=100,
            column_profiles={},
        )
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()
        report: EDAReport = presenter.present_analysis(analysis)
        assert report.overview.duplicate_count == 0

    def test_build_stats_with_unknown_stat_type_passes(self) -> None:
        """_build_stats com tipo Statistic desconhecido não quebra (linha 250 else)."""
        metadata: ColumnMetadata = ColumnMetadata(
            name="unknown",
            data_type=DataType.OTHER,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="unk_stat",
            columns=(metadata,),
            row_count=10,
            column_profiles={
                "unknown": ColumnProfile(
                    metadata=metadata,
                    stats="not_a_real_stat_object",
                    distribution=None,
                    outlier=None,
                ),
            },
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()
        report: EDAReport = presenter.present_analysis(analysis)
        assert len(report.stats.numeric) == 0
        assert len(report.stats.categorical) == 0
        assert len(report.stats.temporal) == 0
        assert len(report.stats.text) == 0
        assert len(report.stats.boolean) == 0

    def test_build_distributions_with_unknown_dist_type_passes(self) -> None:
        """_build_distributions com tipo Distribution desconhecido não quebra (linha 290 else)."""
        metadata: ColumnMetadata = ColumnMetadata(
            name="unknown",
            data_type=DataType.OTHER,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="unk_dist",
            columns=(metadata,),
            row_count=10,
            column_profiles={
                "unknown": ColumnProfile(
                    metadata=metadata,
                    stats=None,
                    distribution="not_a_real_dist_object",
                    outlier=None,
                ),
            },
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()
        report: EDAReport = presenter.present_analysis(analysis)
        assert len(report.distributions.histograms) == 0
        assert len(report.distributions.frequencies) == 0
        assert len(report.distributions.temporal_charts) == 0

    def test_build_stats_with_all_stat_types(self) -> None:
        """_build_stats deve converter CategoricalStats,
        TemporalStats, TextStats e BooleanStats.
        """
        # Arrange
        meta_num: ColumnMetadata = ColumnMetadata(
            name="num",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        meta_cat: ColumnMetadata = ColumnMetadata(
            name="cat",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        meta_tmp: ColumnMetadata = ColumnMetadata(
            name="tmp",
            data_type=DataType.DATE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        meta_txt: ColumnMetadata = ColumnMetadata(
            name="txt",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        meta_bool: ColumnMetadata = ColumnMetadata(
            name="bool",
            data_type=DataType.BOOLEAN,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="all_stats",
            columns=(meta_num, meta_cat, meta_tmp, meta_txt, meta_bool),
            row_count=10,
            column_profiles={
                "num": ColumnProfile(
                    metadata=meta_num,
                    stats=NumericStats(
                        mean=5.0, std=2.0, min=1.0, q25=3.0, q50=5.0, q75=7.0, max=9.0, skewness=0.0, kurtosis=-1.0
                    ),
                    distribution=None,
                    outlier=None,
                ),
                "cat": ColumnProfile(
                    metadata=meta_cat,
                    stats=CategoricalStats(value_counts={"a": 5, "b": 5}, mode="a", cardinality=2, unique_ratio=0.2),
                    distribution=None,
                    outlier=None,
                ),
                "tmp": ColumnProfile(
                    metadata=meta_tmp,
                    stats=TemporalStats(min_date="2024-01-01", max_date="2024-12-31", range_days=365, gap_count=0),
                    distribution=None,
                    outlier=None,
                ),
                "txt": ColumnProfile(
                    metadata=meta_txt,
                    stats=TextStats(min_length=2, max_length=10, avg_length=5.5, empty_ratio=0.0),
                    distribution=None,
                    outlier=None,
                ),
                "bool": ColumnProfile(
                    metadata=meta_bool,
                    stats=BooleanStats(true_count=6, false_count=4, true_ratio=0.6),
                    distribution=None,
                    outlier=None,
                ),
            },
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert
        assert len(report.stats.numeric) == 1
        assert report.stats.numeric[0].column_name == "num"
        assert len(report.stats.categorical) == 1
        assert report.stats.categorical[0].column_name == "cat"
        assert report.stats.categorical[0].mode == "a"
        assert report.stats.categorical[0].top_values == [("a", 5), ("b", 5)]
        assert len(report.stats.temporal) == 1
        assert report.stats.temporal[0].column_name == "tmp"
        assert report.stats.temporal[0].min_date == "2024-01-01"
        assert len(report.stats.text) == 1
        assert report.stats.text[0].column_name == "txt"
        assert report.stats.text[0].avg_length == 5.5
        assert len(report.stats.boolean) == 1
        assert report.stats.boolean[0].column_name == "bool"
        assert report.stats.boolean[0].true_count == 6

    def test_build_distributions_with_all_dist_types(self) -> None:
        """_build_distributions deve converter NumericDistribution,
        CategoricalDistribution e TemporalDistribution.
        """
        # Arrange
        meta_num: ColumnMetadata = ColumnMetadata(
            name="num",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        meta_cat: ColumnMetadata = ColumnMetadata(
            name="cat",
            data_type=DataType.STRING,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        meta_tmp: ColumnMetadata = ColumnMetadata(
            name="tmp",
            data_type=DataType.DATE,
            nullable=True,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="dist_test",
            columns=(meta_num, meta_cat, meta_tmp),
            row_count=10,
            column_profiles={
                "num": ColumnProfile(
                    metadata=meta_num,
                    stats=None,
                    distribution=NumericDistribution(bins=[(0.0, 5.0, 3), (5.0, 10.0, 7)]),
                    outlier=None,
                ),
                "cat": ColumnProfile(
                    metadata=meta_cat,
                    stats=None,
                    distribution=CategoricalDistribution(categories=[("a", 6), ("b", 4)], others_count=0),
                    outlier=None,
                ),
                "tmp": ColumnProfile(
                    metadata=meta_tmp,
                    stats=None,
                    distribution=TemporalDistribution(periods=[("2024-Q1", 4), ("2024-Q2", 6)]),
                    outlier=None,
                ),
            },
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert
        assert "num" in report.distributions.histograms
        assert len(report.distributions.histograms["num"]) == 2
        assert "cat" in report.distributions.frequencies
        assert len(report.distributions.frequencies["cat"]) == 2
        assert "tmp" in report.distributions.temporal_charts
        assert len(report.distributions.temporal_charts["tmp"]) == 2

    def test_build_correlations_with_matrix(self) -> None:
        """_build_correlations deve montar a matrix de correlação
        e definir diagonal como 1.0.
        """
        # Arrange
        metadata: ColumnMetadata = ColumnMetadata(
            name="a",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="corr_test",
            columns=(metadata,),
            row_count=10,
            column_profiles={"a": ColumnProfile(metadata=metadata, stats=None, distribution=None, outlier=None)},
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        corr: Correlation = Correlation(
            column_a="a",
            column_b="a",
            method=CorrelationMethod.PEARSON,
            value=1.0,
        )
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[corr],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert
        assert report.correlations.method == "pearson"
        assert "a" in report.correlations.matrix
        assert report.correlations.matrix["a"]["a"] == 1.0

    def test_build_correlations_with_multiple_entries(self) -> None:
        """_build_correlations com múltiplas entradas deve preencher
        matrix simetricamente e diagonal.
        """
        # Arrange
        meta_a: ColumnMetadata = ColumnMetadata(
            name="a",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        meta_b: ColumnMetadata = ColumnMetadata(
            name="b",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="corr2",
            columns=(meta_a, meta_b),
            row_count=10,
            column_profiles={
                "a": ColumnProfile(metadata=meta_a, stats=None, distribution=None, outlier=None),
                "b": ColumnProfile(metadata=meta_b, stats=None, distribution=None, outlier=None),
            },
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        corr: Correlation = Correlation(
            column_a="a",
            column_b="b",
            method=CorrelationMethod.PEARSON,
            value=0.85,
        )
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[corr],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert
        assert report.correlations.matrix["a"]["b"] == 0.85
        assert report.correlations.matrix["b"]["a"] == 0.85
        assert report.correlations.matrix["a"]["a"] == 1.0
        assert report.correlations.matrix["b"]["b"] == 1.0

    def test_build_outliers_with_data(self) -> None:
        """_build_outliers deve incluir colunas com OutlierInfo."""
        # Arrange
        metadata: ColumnMetadata = ColumnMetadata(
            name="x",
            data_type=DataType.INTEGER,
            nullable=False,
            inferred_type=None,
            null_count=0,
            non_null_count=10,
        )
        data_profile: DataProfile = DataProfile(
            id="out_test",
            columns=(metadata,),
            row_count=10,
            column_profiles={
                "x": ColumnProfile(
                    metadata=metadata,
                    stats=None,
                    distribution=None,
                    outlier=OutlierInfo(
                        method=OutlierMethod.IQR,
                        count=1,
                        ratio=0.1,
                        bounds_lower=-5.0,
                        bounds_upper=15.0,
                    ),
                ),
            },
        )
        quality: QualityScore = QualityScore(overall=100.0, dimensions={}, top_penalizers=[])
        analysis: DatasetAnalysis = DatasetAnalysis(
            profile=data_profile,
            quality=quality,
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime(2024, 6, 1),
        )
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        report: EDAReport = presenter.present_analysis(analysis)

        # Assert
        assert len(report.outliers.outliers) == 1
        assert report.outliers.outliers[0].column_name == "x"
        assert report.outliers.outliers[0].method == "iqr"
        assert report.outliers.outliers[0].count == 1
        assert report.outliers.outliers[0].ratio == 0.1

    def test_present_quality_with_empty_dimensions(self) -> None:
        """present_quality com dimensões vazias deve retornar
        QualityReport vazio.
        """
        # Arrange
        quality: QualityScore = QualityScore(overall=0.0, dimensions={}, top_penalizers=[])
        presenter: AnalysisPresenter = AnalysisPresenter()

        # Act
        result: QualityReport = presenter.present_quality(quality)

        # Assert
        assert isinstance(result, QualityReport)
        assert result.overall == 0.0
        assert len(result.dimensions) == 0


class TestQualityPresenter:
    """Testes para o presenter de qualidade."""

    def test_present_quality_returns_quality_report(self) -> None:
        """O método present_quality deve retornar um QualityReport com
        overall, dimensões e top_penalizers.
        """
        # Arrange
        factor: QualityFactor = QualityFactor(
            name="Proporção de nulos",
            score=0.85,
            internal_weight=1.0,
            contribution=0.85,
            reason="15% de nulos",
            severity=Severity.MEDIUM,
            affected_columns=["col_a"],
        )
        dimension: QualityDimension = QualityDimension(
            name="completude",
            score=85.0,
            weight=0.3,
            contribution=25.5,
            factors=[factor],
        )
        quality: QualityScore = QualityScore(
            overall=85.0,
            dimensions={"completude": dimension},
            top_penalizers=[factor],
        )
        presenter: QualityPresenter = QualityPresenter()

        # Act
        report: QualityReport = presenter.present_quality(quality)

        # Assert
        assert isinstance(report, QualityReport)
        assert report.overall == 85.0
        assert len(report.dimensions) == 1
        assert report.dimensions[0].name == "completude"
        assert report.dimensions[0].score == 85.0
        assert len(report.dimensions[0].factors) == 1
        assert report.dimensions[0].factors[0].name == "Proporção de nulos"
        assert report.dimensions[0].factors[0].score == 0.85
        assert len(report.top_penalizers) == 1
        assert report.top_penalizers[0].name == "Proporção de nulos"

    def test_present_quality_present_analysis_raises(self) -> None:
        """QualityPresenter.present_analysis deve levantar
        NotImplementedError.
        """
        # Arrange
        presenter: QualityPresenter = QualityPresenter()

        # Act & Assert
        with pytest.raises(NotImplementedError):
            presenter.present_analysis(mock.Mock())  # type: ignore[arg-type]
