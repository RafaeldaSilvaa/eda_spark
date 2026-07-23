from __future__ import annotations

"""Testes para o caso de uso AnalyzeDatasetUseCase.

Testa a orquestração do fluxo de análise exploratória completa,
utilizando mocks para todas as dependências externas.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, create_autospec

from spark_eda.application.use_cases.analyze_dataset import AnalyzeDatasetUseCase, AnalyzeRequest
from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.domain.entities.dataset_analysis import DatasetAnalysis
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.insight_engine import InsightEngine
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.domain.services.recommendation_engine import RecommendationEngine


class TestAnalyzeDatasetUseCase:
    """Testes para o caso de uso de análise exploratória completa."""

    def test_execute_calls_data_provider_and_services(self) -> None:
        """O método execute deve chamar o data provider para perfilamento e
        todos os serviços de domínio na sequência correta.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock()

        quality_calculator.calculate.return_value = QualityScore(
            overall=95.0,
            dimensions={},
            top_penalizers=[],
        )
        insight_engine.generate.return_value = []
        recommendation_engine.generate.return_value = []

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        result: DatasetAnalysis = use_case.execute(request, dataframe)

        data_provider.compute_fingerprint.assert_called_once_with(
            dataframe,
            request.config,
        )
        cache_provider.get.assert_called_once()
        data_provider.compute_profile.assert_called_once_with(
            dataframe,
            request.columns,
            request.config,
        )
        quality_calculator.calculate.assert_called_once()
        insight_engine.generate.assert_called_once()
        recommendation_engine.generate.assert_called_once()
        assert isinstance(result, DatasetAnalysis)

    def test_execute_returns_cached_result_when_available(self) -> None:
        """Quando o cache contém um DatasetAnalysis para a chave
        calculada, o resultado deve ser retornado sem chamar o data
        provider para perfilamento.
        """
        cached_analysis: DatasetAnalysis = DatasetAnalysis(
            profile=MagicMock(),
            quality=MagicMock(),
            correlations=[],
            insights=[],
            recommendations=[],
            timestamps=datetime.now(timezone.utc),
        )
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = cached_analysis

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        result: DatasetAnalysis = use_case.execute(request, dataframe)

        data_provider.compute_profile.assert_not_called()
        quality_calculator.calculate.assert_not_called()
        insight_engine.generate.assert_not_called()
        recommendation_engine.generate.assert_not_called()
        assert result is cached_analysis

    def test_execute_stores_result_in_cache_on_miss(self) -> None:
        """Quando o cache não contém o resultado, o DatasetAnalysis
        computado deve ser armazenado no cache.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock()
        quality_calculator.calculate.return_value = MagicMock()
        insight_engine.generate.return_value = []
        recommendation_engine.generate.return_value = []

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        use_case.execute(request, dataframe)

        cache_provider.set.assert_called_once()

    def test_execute_propagates_provider_error(self) -> None:
        """Quando o data provider lança uma exceção durante o
        perfilamento, a exceção deve ser propagada.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = None
        data_provider.compute_profile.side_effect = ValueError(
            "Coluna 'inexistente' não encontrada no schema",
        )

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        import pytest

        with pytest.raises(ValueError, match="inexistente"):
            use_case.execute(request, dataframe)
