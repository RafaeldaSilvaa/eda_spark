from __future__ import annotations

"""Testes para o caso de uso AssessQualityUseCase.

Testa a orquestração do fluxo de avaliação de qualidade,
utilizando mocks para todas as dependências externas.
"""

from unittest.mock import MagicMock, create_autospec

from spark_eda.application.use_cases.assess_quality import AssessQualityUseCase, QualityRequest
from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.quality_calculator import QualityCalculator


class TestAssessQualityUseCase:
    """Testes para o caso de uso de avaliação de qualidade."""

    def test_execute_calls_data_provider_and_quality_calculator(self) -> None:
        """O método execute deve chamar o data provider para fingerprint e
        perfilamento, e o quality calculator para cálculo da qualidade.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock()

        quality_score: QualityScore = QualityScore(
            overall=85.0,
            dimensions={},
            top_penalizers=[],
        )
        quality_calculator.calculate.return_value = quality_score

        use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
        )

        request: QualityRequest = QualityRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        result: QualityScore = use_case.execute(request, dataframe)

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
        assert result is quality_score

    def test_execute_returns_cached_quality_when_available(self) -> None:
        """Quando o cache contém um QualityScore para a chave calculada,
        o resultado deve ser retornado sem chamar o data provider para
        perfilamento.
        """
        cached_quality: QualityScore = QualityScore(
            overall=90.0,
            dimensions={},
            top_penalizers=[],
        )
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)

        data_provider.compute_fingerprint.return_value = "fp_abc123"
        cache_provider.get.return_value = cached_quality

        use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
        )

        request: QualityRequest = QualityRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        result: QualityScore = use_case.execute(request, dataframe)

        data_provider.compute_profile.assert_not_called()
        quality_calculator.calculate.assert_not_called()
        assert result is cached_quality
