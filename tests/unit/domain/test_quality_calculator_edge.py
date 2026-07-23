from __future__ import annotations

"""Testes de borda para a calculadora de qualidade.

Cobre o branch onde a lista de fatores de uma dimensão está vazia,
resultando em score 100.0 e contribution = weight * 100.
"""

from spark_eda.domain.entities.quality_score import QualityFactor, QualityDimension
from spark_eda.domain.services.quality_calculator import QualityCalculator, DIMENSION_WEIGHTS


class TestQualityCalculatorEdge:
    def test_compute_dimension_with_empty_factors(self) -> None:
        """Dimensão sem fatores retorna score 100.0 e contribution = peso * 100 (linha 61)."""
        calculator: QualityCalculator = QualityCalculator()
        dimension: QualityDimension = calculator._compute_dimension_score(
            dimension_name="completeness",
            factors=[],
        )
        assert dimension.score == 100.0
        assert dimension.weight == DIMENSION_WEIGHTS.get("completeness", 0.0)
        expected_contribution: float = DIMENSION_WEIGHTS.get("completeness", 0.0) * 100.0
        assert dimension.contribution == expected_contribution
        assert dimension.factors == []