from __future__ import annotations

"""Testes que cobrem as últimas linhas não testadas nos casos de uso.

Cobre:
- analyze_dataset: linhas 117-118 (cache set com falha)
- analyze_dataset: linhas 161-162 (compute_profile com exceção não-ValueError)
- assess_quality: linhas 87-88 (cache get com falha)
- assess_quality: linhas 107-108 (cache set com falha)
"""

from unittest.mock import MagicMock, create_autospec

import pytest

from spark_eda.application.exceptions import DataProviderError
from spark_eda.application.ports.cache_provider import CacheProvider
from spark_eda.application.ports.data_provider import DataProvider
from spark_eda.application.use_cases.analyze_dataset import AnalyzeDatasetUseCase, AnalyzeRequest
from spark_eda.application.use_cases.assess_quality import AssessQualityUseCase, QualityRequest
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.services.insight_engine import InsightEngine
from spark_eda.domain.services.quality_calculator import QualityCalculator
from spark_eda.domain.services.recommendation_engine import RecommendationEngine


class TestAnalyzeRemainingCoverage:
    """Cobre as linhas 117-118 e 161-162 do analyze_dataset.py."""

    def test_cache_set_failure_logs_warning(self) -> None:
        """cache_provider.set lançando exceção não deve interromper o fluxo."""
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        cache_provider.set.side_effect = RuntimeError("Cache cheio")
        calc: MagicMock = MagicMock(spec=QualityCalculator)
        ie: MagicMock = MagicMock(spec=InsightEngine)
        re: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock(spec=DataProfile)
        calc.calculate.return_value = MagicMock(spec=QualityScore)
        ie.generate.return_value = []
        re.generate.return_value = []

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider, cache_provider=cache_provider,
            quality_calculator=calc, insight_engine=ie, recommendation_engine=re,
        )

        result = use_case.execute(AnalyzeRequest(columns=None, config=MagicMock()), MagicMock())

        assert result is not None
        cache_provider.set.assert_called_once()

    def test_non_value_error_from_compute_profile_wraps_in_runtime_error(self) -> None:
        """compute_profile lançando Exception (não ValueError) deve ser envolvido em RuntimeError."""
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        calc: MagicMock = MagicMock(spec=QualityCalculator)
        ie: MagicMock = MagicMock(spec=InsightEngine)
        re: MagicMock = MagicMock(spec=RecommendationEngine)

        data_provider.compute_fingerprint.return_value = "fp"
        cache_provider.get.return_value = None
        data_provider.compute_profile.side_effect = RuntimeError("Spark falhou")

        use_case: AnalyzeDatasetUseCase = AnalyzeDatasetUseCase(
            data_provider=data_provider, cache_provider=cache_provider,
            quality_calculator=calc, insight_engine=ie, recommendation_engine=re,
        )

        with pytest.raises(DataProviderError, match="Failed to compute dataset profile"):
            use_case.execute(AnalyzeRequest(columns=None, config=MagicMock()), MagicMock())


class TestAssessQualityRemainingCoverage:
    """Cobre as linhas 87-88 e 107-108 do assess_quality.py."""

    def test_cache_get_failure_logs_warning_and_continues(self) -> None:
        """cache_provider.get lançando exceção deve logar e continuar."""
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        calc: MagicMock = MagicMock(spec=QualityCalculator)

        data_provider.compute_fingerprint.return_value = "fp"
        cache_provider.get.side_effect = RuntimeError("Cache offline")
        data_provider.compute_profile.return_value = MagicMock(spec=DataProfile)
        calc.calculate.return_value = MagicMock(spec=QualityScore)

        use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=data_provider, cache_provider=cache_provider,
            quality_calculator=calc,
        )

        result = use_case.execute(QualityRequest(columns=None, config=MagicMock()), MagicMock())

        assert result is not None

    def test_cache_set_failure_logs_warning(self) -> None:
        """cache_provider.set lançando exceção não deve interromper o fluxo."""
        data_provider: MagicMock = create_autospec(DataProvider)
        cache_provider: MagicMock = create_autospec(CacheProvider)
        calc: MagicMock = MagicMock(spec=QualityCalculator)

        data_provider.compute_fingerprint.return_value = "fp"
        cache_provider.get.return_value = None
        data_provider.compute_profile.return_value = MagicMock(spec=DataProfile)
        calc.calculate.return_value = MagicMock(spec=QualityScore)
        cache_provider.set.side_effect = RuntimeError("Cache offline")

        use_case: AssessQualityUseCase = AssessQualityUseCase(
            data_provider=data_provider, cache_provider=cache_provider,
            quality_calculator=calc,
        )

        result = use_case.execute(QualityRequest(columns=None, config=MagicMock()), MagicMock())

        assert result is not None
        cache_provider.set.assert_called_once()
