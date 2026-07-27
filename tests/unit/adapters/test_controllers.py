from __future__ import annotations

"""Testes para os controladores de análise e qualidade.

Testa inicialização e validação de parâmetros, sem dependência
de Spark (as chamadas que exigem PySpark não são executadas).
"""

from unittest import mock

import pytest

from spark_eda.adapters.controllers.analyze_controller import AnalyzeController
from spark_eda.adapters.controllers.quality_controller import QualityController
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.application.dto.quality_section import QualityReport


class TestAnalyzeController:
    """Testes para o controlador de análise exploratória."""

    def test_init_creates_all_dependencies(self) -> None:
        """A inicialização do AnalyzeController deve criar todas as
        dependências internas sem erro.
        """
        # Arrange & Act
        controller: AnalyzeController = AnalyzeController(cache_max_size=5)

        # Assert
        assert controller is not None

    def test_init_with_default_cache_size(self) -> None:
        """A inicialização com cache_max_size padrão deve funcionar."""
        # Arrange & Act
        controller: AnalyzeController = AnalyzeController()

        # Assert
        assert controller is not None

    def test_execute_with_none_dataframe_raises_value_error(self) -> None:
        """executar com DataFrame None deve levantar ValueError."""
        # Arrange
        controller: AnalyzeController = AnalyzeController()

        # Act & Assert
        with pytest.raises(ValueError, match="DataFrame cannot be None"):
            controller.execute(dataframe=None)  # type: ignore[arg-type]

    def test_execute_with_valid_dataframe_returns_eda_report(self) -> None:
        """execute com DataFrame mockado deve retornar EDAReport."""
        # Arrange
        controller: AnalyzeController = AnalyzeController()
        mock_df: mock.MagicMock = mock.MagicMock()
        mock_report: mock.MagicMock = mock.MagicMock(spec=EDAReport)
        mock_report.insights = mock.MagicMock()
        mock_report.insights.insights = []
        mock_report.recommendations = mock.MagicMock()
        mock_report.recommendations.recommendations = []
        controller._presenter.present_analysis = mock.MagicMock(return_value=mock_report)
        controller._use_case.execute = mock.MagicMock(return_value=mock.MagicMock())

        # Act
        result: EDAReport = controller.execute(dataframe=mock_df)

        # Assert
        assert result is mock_report
        controller._use_case.execute.assert_called_once()
        controller._presenter.present_analysis.assert_called_once()

    def test_execute_propagates_data_provider_value_error(self) -> None:
        """execute deve propagar ValueError do data_provider."""
        # Arrange
        controller: AnalyzeController = AnalyzeController()
        mock_df: mock.MagicMock = mock.MagicMock()
        controller._use_case.execute = mock.MagicMock(
            side_effect=ValueError("coluna nao encontrada"),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="coluna nao encontrada"):
            controller.execute(dataframe=mock_df)

    def test_execute_with_custom_config(self) -> None:
        """execute com config personalizada deve usá-la."""
        # Arrange
        controller: AnalyzeController = AnalyzeController()
        mock_df: mock.MagicMock = mock.MagicMock()
        mock_report: mock.MagicMock = mock.MagicMock(spec=EDAReport)
        mock_report.insights = mock.MagicMock()
        mock_report.insights.insights = []
        mock_report.recommendations = mock.MagicMock()
        mock_report.recommendations.recommendations = []
        controller._presenter.present_analysis = mock.MagicMock(return_value=mock_report)
        controller._use_case.execute = mock.MagicMock(return_value=mock.MagicMock())
        from spark_eda.framework.config import EDAConfig

        config: EDAConfig = EDAConfig(max_categories=10)

        # Act
        result: EDAReport = controller.execute(dataframe=mock_df, config=config)

        # Assert
        assert result is mock_report


class TestQualityController:
    """Testes para o controlador de avaliação de qualidade."""

    def test_init_creates_all_dependencies(self) -> None:
        """A inicialização do QualityController deve criar todas as
        dependências internas sem erro.
        """
        # Arrange & Act
        controller: QualityController = QualityController(cache_max_size=5)

        # Assert
        assert controller is not None

    def test_init_with_default_cache_size(self) -> None:
        """A inicialização com cache_max_size padrão deve funcionar."""
        # Arrange & Act
        controller: QualityController = QualityController()

        # Assert
        assert controller is not None

    def test_execute_with_none_dataframe_raises_value_error(self) -> None:
        """executar com DataFrame None deve levantar ValueError."""
        # Arrange
        controller: QualityController = QualityController()

        # Act & Assert
        with pytest.raises(ValueError, match="DataFrame cannot be None"):
            controller.execute(dataframe=None)  # type: ignore[arg-type]

    def test_execute_with_valid_dataframe_returns_quality_report(self) -> None:
        """execute com DataFrame mockado deve retornar QualityReport."""
        # Arrange
        controller: QualityController = QualityController()
        mock_df: mock.MagicMock = mock.MagicMock()
        mock_quality: mock.MagicMock = mock.MagicMock(spec=QualityReport)
        mock_quality.overall = 85.0
        controller._presenter.present_quality = mock.MagicMock(return_value=mock_quality)
        controller._use_case.execute = mock.MagicMock(return_value=mock.MagicMock())

        # Act
        result: QualityReport = controller.execute(dataframe=mock_df)

        # Assert
        assert result is mock_quality
        assert result.overall == 85.0
        controller._use_case.execute.assert_called_once()
        controller._presenter.present_quality.assert_called_once()

    def test_execute_propagates_data_provider_value_error(self) -> None:
        """execute deve propagar ValueError do data_provider."""
        # Arrange
        controller: QualityController = QualityController()
        mock_df: mock.MagicMock = mock.MagicMock()
        controller._use_case.execute = mock.MagicMock(
            side_effect=ValueError("coluna nao encontrada"),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="coluna nao encontrada"):
            controller.execute(dataframe=mock_df)
