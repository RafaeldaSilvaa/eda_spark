from __future__ import annotations

"""Testes de integração para o AnalysisPresenter com AI.

Testa o fluxo de commentary AI no presenter: ai_enabled toggle,
falhas do OmniRouteManager e sucesso completo.
"""

from unittest import mock

from spark_eda.adapters.omniroute.models import AiCommentary
from spark_eda.adapters.presenters.analysis_presenter import AnalysisPresenter
from spark_eda.application.dto.eda_report import EDAReport
from spark_eda.framework.config import EDAConfig


def _make_mock_analysis() -> mock.MagicMock:
    """Cria um DatasetAnalysis mockado com todas as seções."""
    analysis = mock.MagicMock()
    analysis.profile.row_count = 100
    analysis.profile.columns = ()
    analysis.quality.overall = 95.0
    analysis.quality.dimensions = {}
    analysis.quality.top_penalizers = []
    return analysis


class TestAnalysisPresenterAI:
    """Testes para o comportamento de AI commentary no AnalysisPresenter."""

    def test_ai_disabled_no_manager_initialized(self) -> None:
        """present deve pular toda a lógica AI quando
        ai_enabled=False, sem chamar OmniRouteManager."""
        analysis = _make_mock_analysis()
        config = EDAConfig(ai_enabled=False)

        with (
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteManager") as mock_manager_cls,
        ):
            presenter = AnalysisPresenter()
            report = presenter.present(analysis, config=config)

            assert report.commentary is None
            mock_manager_cls.assert_not_called()

    def test_ai_enabled_but_manager_fails_returns_without_commentary(self) -> None:
        """present deve retornar relatório sem commentary quando
        OmniRouteManager.ensure_running retorna False."""
        analysis = _make_mock_analysis()
        config = EDAConfig(ai_enabled=True)

        with (
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteManager") as mock_manager_cls,
        ):
            mock_manager = mock.MagicMock()
            mock_manager.ensure_running.return_value = False
            mock_manager_cls.return_value = mock_manager

            presenter = AnalysisPresenter()
            report = presenter.present(analysis, config=config)

            assert report.commentary is None
            mock_manager.ensure_running.assert_called_once()

    def test_ai_enabled_full_success_attaches_commentary(self) -> None:
        """present deve retornar relatório com AiCommentary
        quando OmniRoute está disponível e responde."""
        analysis = _make_mock_analysis()
        config = EDAConfig(ai_enabled=True)
        expected_commentary = AiCommentary(
            overview="AI overview",
            executive_analysis="Executive analysis",
        )

        with (
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteManager") as mock_manager_cls,
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteClient") as mock_client_cls,
        ):
            mock_manager = mock.MagicMock()
            mock_manager.ensure_running.return_value = True
            mock_manager_cls.return_value = mock_manager

            mock_client = mock.MagicMock()
            mock_client.analyze.return_value = expected_commentary
            mock_client_cls.return_value = mock_client

            presenter = AnalysisPresenter()
            report = presenter.present(analysis, config=config)

            assert report.commentary is not None
            assert report.commentary.overview == "AI overview"
            assert report.commentary.executive_analysis == "Executive analysis"
            mock_manager.ensure_running.assert_called_once()
            mock_client.analyze.assert_called_once()

    def test_present_analysis_also_handles_config(self) -> None:
        """present_analysis deve aceitar config e propagar para
        present."""
        analysis = _make_mock_analysis()
        config = EDAConfig(ai_enabled=False)

        with mock.patch.object(AnalysisPresenter, "present") as mock_present:
            mock_present.return_value = mock.MagicMock(spec=EDAReport)

            presenter = AnalysisPresenter()
            presenter.present_analysis(analysis, config=config)

            mock_present.assert_called_once_with(analysis, config=config)

    def test_ai_enabled_uses_config_url_and_timeout(self) -> None:
        """present deve usar omniroute_url e omniroute_timeout
        do config ao criar o client."""
        analysis = _make_mock_analysis()
        config = EDAConfig(ai_enabled=True, omniroute_url="http://custom:9999/v1", omniroute_timeout=60)

        with (
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteManager") as mock_manager_cls,
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteClient") as mock_client_cls,
        ):
            mock_manager = mock.MagicMock()
            mock_manager.ensure_running.return_value = True
            mock_manager_cls.return_value = mock_manager

            mock_client = mock.MagicMock()
            mock_client.analyze.return_value = AiCommentary()
            mock_client_cls.return_value = mock_client

            presenter = AnalysisPresenter()
            presenter.present(analysis, config=config)

            mock_client_cls.assert_called_once_with("http://custom:9999/v1", 60)

    def test_ai_enabled_default_url_and_timeout(self) -> None:
        """present deve usar URL e timeout padrão quando não
        configurados explicitamente."""
        analysis = _make_mock_analysis()
        config = EDAConfig(ai_enabled=True)

        with (
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteManager") as mock_manager_cls,
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteClient") as mock_client_cls,
        ):
            mock_manager = mock.MagicMock()
            mock_manager.ensure_running.return_value = True
            mock_manager_cls.return_value = mock_manager

            mock_client = mock.MagicMock()
            mock_client.analyze.return_value = AiCommentary()
            mock_client_cls.return_value = mock_client

            presenter = AnalysisPresenter()
            presenter.present(analysis, config=config)

            mock_client_cls.assert_called_once_with("http://localhost:20128/v1", 30)

    def test_present_analysis_without_config_skips_ai(self) -> None:
        """present_analysis sem config deve pular AI injection
        (config=None significa AI desligado)."""
        analysis = _make_mock_analysis()

        with (
            mock.patch("spark_eda.adapters.presenters.analysis_presenter.OmniRouteManager") as mock_manager_cls,
        ):
            presenter = AnalysisPresenter()
            report = presenter.present_analysis(analysis)

            # config=None, so AI injection is skipped entirely
            mock_manager_cls.assert_not_called()
            assert report.commentary is None
