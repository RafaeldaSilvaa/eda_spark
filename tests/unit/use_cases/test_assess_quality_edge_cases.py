from __future__ import annotations

"""Testes de borda para o caso de uso AssessQualityUseCase.

Testa cenários de falha no data provider e quality calculator,
além do comportamento do cache em caso de miss.
"""

from unittest.mock import MagicMock, create_autospec

import pytest

from spark_eda.application.exceptions import DataProviderError, QualityError
from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.application.use_cases.assess_quality import AssessQualityUseCase, QualityRequest
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.quality_calculator import QualityCalculator


class TestAssessQualityEdgeCases:
    """Testes de borda para o caso de uso de avaliação de qualidade."""

    def test_execute_raises_runtime_error_when_data_provider_fails(
        self,
    ) -> None:
        """Quando o data provider lança exceção, o erro é envolvido em
        DataProviderError.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)

        data_provider.compute_fingerprint.return_value = "fp_abc"
        cache_provider.get.return_value = None

        use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
        )
        request: QualityRequest = QualityRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        data_provider.compute_profile.side_effect = ValueError("Coluna inválida")
        with pytest.raises(DataProviderError, match="Failed to compute dataset profile"):
            use_case.execute(request, dataframe)

        data_provider.compute_profile.side_effect = Exception("Erro inesperado")
        with pytest.raises(DataProviderError, match="Failed to compute dataset profile"):
            use_case.execute(request, dataframe)

    def test_execute_raises_runtime_error_when_quality_calculator_fails(
        self,
    ) -> None:
        """Quando o quality_calculator.calculate lança uma exceção,
        o erro deve ser envolvido em RuntimeError.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)

        data_provider.compute_fingerprint.return_value = "fp_abc"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock()
        quality_calculator.calculate.side_effect = Exception("Erro no cálculo")

        use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
        )

        request: QualityRequest = QualityRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        with pytest.raises(QualityError, match="Failed to calculate data quality"):
            use_case.execute(request, dataframe)

    def test_execute_cache_miss_computes_and_caches(self) -> None:
        """Quando o cache não contém o resultado, o fluxo completo
        de perfilamento e cálculo deve ser executado, e o resultado
        armazenado no cache.
        """
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        quality_calculator: MagicMock = MagicMock(spec=QualityCalculator)

        data_provider.compute_fingerprint.return_value = "fp_abc"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock()
        quality_calculator.calculate.return_value = MagicMock(spec=QualityScore)

        use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=data_provider,
            cache_provider=cache_provider,
            quality_calculator=quality_calculator,
        )

        request: QualityRequest = QualityRequest(columns=None, config=MagicMock())
        dataframe = MagicMock()

        use_case.execute(request, dataframe)

        data_provider.compute_profile.assert_called_once()
        quality_calculator.calculate.assert_called_once()
        cache_provider.set.assert_called_once()
