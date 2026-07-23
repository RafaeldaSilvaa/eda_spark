from __future__ import annotations

"""Testes de borda para o caso de uso AnalyzeDatasetUseCase.

Testa cenários de falha em cada etapa da orquestração e
comportamento do método _build_cache_key com diferentes
configurações de colunas.
"""

from unittest.mock import MagicMock, create_autospec

import pytest

from spark_eda.application.use_cases.analyze_dataset import AnalyzeDatasetUseCase, AnalyzeRequest
from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.insight_engine import InsightEngine
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.domain.services.recommendation_engine import RecommendationEngine


class TestAnalyzeDatasetEdgeCases:
    """Testes de borda para o caso de uso de análise exploratória."""

    def test_execute_raises_value_error_when_data_provider_fails_with_value_error(
        self,
    ) -> None:
        """Quando o data provider lança ValueError durante o perfilamento,
        a exceção deve ser re-lançada sem wrapping.
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

        with pytest.raises(ValueError, match="inexistente"):
            use_case.execute(request, dataframe)

    def test_execute_raises_runtime_error_when_cache_get_fails(self) -> None:
        """Quando o cache_provider.get lança uma exceção, o use case
        deve logar um warning e continuar o fluxo normalmente,
        computando o resultado sem propagar o erro.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.side_effect = RuntimeError("Cache indisponível")
        data_provider.compute_profile.return_value = MagicMock(spec=DataProfile)
        quality_calculator.calculate.return_value = MagicMock(spec=QualityScore)
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

        data_provider.compute_profile.assert_called_once()
        quality_calculator.calculate.assert_called_once()
        insight_engine.generate.assert_called_once()
        recommendation_engine.generate.assert_called_once()

    def test_execute_raises_runtime_error_when_quality_calculator_fails(
        self,
    ) -> None:
        """Quando o quality_calculator.calculate lança uma exceção,
        o erro deve ser envolvido em RuntimeError.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock(spec=DataProfile)
        quality_calculator.calculate.side_effect = Exception("Erro no cálculo de qualidade")

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        with pytest.raises(RuntimeError, match="Failed to calculate data quality"):
            use_case.execute(request, dataframe)

    def test_execute_raises_runtime_error_when_insight_engine_fails(
        self,
    ) -> None:
        """Quando o insight_engine.generate lança uma exceção,
        o erro deve ser envolvido em RuntimeError.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock(spec=DataProfile)
        quality_calculator.calculate.return_value = MagicMock(spec=QualityScore)
        insight_engine.generate.side_effect = Exception("Erro ao gerar insights")

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        with pytest.raises(RuntimeError, match="Failed to generate insights"):
            use_case.execute(request, dataframe)

    def test_execute_raises_runtime_error_when_recommendation_engine_fails(
        self,
    ) -> None:
        """Quando o recommendation_engine.generate lança uma exceção,
        o erro deve ser envolvido em RuntimeError.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock(spec=DataProfile)
        quality_calculator.calculate.return_value = MagicMock(spec=QualityScore)
        insight_engine.generate.return_value = []
        recommendation_engine.generate.side_effect = Exception("Erro ao gerar recomendações")

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        with pytest.raises(RuntimeError, match="Failed to generate recommendations"):
            use_case.execute(request, dataframe)

    def test_build_cache_key_with_all_columns(self) -> None:
        """Quando request.columns é None, a chave de cache deve
        conter \"all\" no lugar das colunas.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(columns=None, config=MagicMock())
        key: str = use_case._build_cache_key(request, "fp_xyz")

        assert key == "analysis:fp_xyz:all"

    def test_build_cache_key_with_specific_columns(self) -> None:
        """Quando request.columns contém colunas específicas, a
        chave de cache deve contê-las ordenadas alfabeticamente.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)
        insight_engine: MagicMock = MagicMock(spec=InsightEngine)
        recommendation_engine: MagicMock = MagicMock(spec=RecommendationEngine)

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
            insight_engine=insight_engine,
            recommendation_engine=recommendation_engine,
        )

        request: AnalyzeRequest = AnalyzeRequest(
            columns=["b", "a"],
            config=MagicMock(),
        )
        key: str = use_case._build_cache_key(request, "fp_xyz")

        assert key == "analysis:fp_xyz:a_b"
