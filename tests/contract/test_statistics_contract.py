from __future__ import annotations

"""Testes de contrato para os tipos de estatísticas do domínio.

Verifica que cada dataclass de estatística (`NumericStats`,
`CategoricalStats`, `TemporalStats`, `TextStats`, `BooleanStats`)
pode ser instanciada com todos os campos e que os tipos dos
campos estão corretos.
"""


import pytest

from spark_eda.domain.entities.statistic import (
    BooleanStats,
    CategoricalStats,
    NumericStats,
    TemporalStats,
    TextStats,
)

pytestmark = pytest.mark.contract


class TestNumericStatsContract:
    """Testes de contrato para :class:`NumericStats`."""

    def test_numeric_stats_creation(self) -> None:
        """Verifica que NumericStats é criada com todos os campos obrigatórios."""
        # Arrange
        mean_expected: float = 25.5
        std_expected: float = 10.2
        min_expected: float = 1.0
        q25_expected: float = 15.0
        q50_expected: float = 25.0
        q75_expected: float = 35.0
        max_expected: float = 50.0
        skewness_expected: float = 0.5
        kurtosis_expected: float = -0.2

        # Act
        stats: NumericStats = NumericStats(
            mean=mean_expected,
            std=std_expected,
            min=min_expected,
            q25=q25_expected,
            q50=q50_expected,
            q75=q75_expected,
            max=max_expected,
            skewness=skewness_expected,
            kurtosis=kurtosis_expected,
        )

        # Assert
        assert stats.mean == mean_expected
        assert stats.std == std_expected
        assert stats.min == min_expected
        assert stats.q25 == q25_expected
        assert stats.q50 == q50_expected
        assert stats.q75 == q75_expected
        assert stats.max == max_expected
        assert stats.skewness == skewness_expected
        assert stats.kurtosis == kurtosis_expected

    def test_numeric_stats_is_frozen(self) -> None:
        """Verifica que NumericStats é imutável (frozen=True)."""
        # Arrange
        stats: NumericStats = NumericStats(
            mean=1.0,
            std=0.5,
            min=0.0,
            q25=0.25,
            q50=0.5,
            q75=0.75,
            max=1.0,
            skewness=0.0,
            kurtosis=0.0,
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            stats.mean = 99.0  # type: ignore[misc]


class TestCategoricalStatsContract:
    """Testes de contrato para :class:`CategoricalStats`."""

    def test_categorical_stats_creation(self) -> None:
        """Verifica que CategoricalStats é criada com todos os campos."""
        # Arrange
        value_counts_expected: dict[str, int] = {"A": 10, "B": 5, "C": 2}
        mode_expected: str = "A"
        cardinality_expected: int = 3
        unique_ratio_expected: float = 0.1765

        # Act
        stats: CategoricalStats = CategoricalStats(
            value_counts=value_counts_expected,
            mode=mode_expected,
            cardinality=cardinality_expected,
            unique_ratio=unique_ratio_expected,
        )

        # Assert
        assert stats.value_counts == value_counts_expected
        assert stats.mode == mode_expected
        assert stats.cardinality == cardinality_expected
        assert stats.unique_ratio == unique_ratio_expected

    def test_categorical_stats_mode_none(self) -> None:
        """Verifica que mode pode ser None quando value_counts está vazio."""
        # Arrange
        ...

        # Act
        stats: CategoricalStats = CategoricalStats(
            value_counts={},
            mode=None,
            cardinality=0,
            unique_ratio=0.0,
        )

        # Assert
        assert stats.mode is None
        assert stats.cardinality == 0


class TestTemporalStatsContract:
    """Testes de contrato para :class:`TemporalStats`."""

    def test_temporal_stats_creation(self) -> None:
        """Verifica que TemporalStats é criada com todos os campos."""
        # Arrange
        min_date_expected: str = "2024-01-01"
        max_date_expected: str = "2024-12-31"
        range_days_expected: int = 365
        gap_count_expected: int = 5

        # Act
        stats: TemporalStats = TemporalStats(
            min_date=min_date_expected,
            max_date=max_date_expected,
            range_days=range_days_expected,
            gap_count=gap_count_expected,
        )

        # Assert
        assert stats.min_date == min_date_expected
        assert stats.max_date == max_date_expected
        assert stats.range_days == range_days_expected
        assert stats.gap_count == gap_count_expected


class TestTextStatsContract:
    """Testes de contrato para :class:`TextStats`."""

    def test_text_stats_creation(self) -> None:
        """Verifica que TextStats é criada com todos os campos."""
        # Arrange
        min_length_expected: int = 3
        max_length_expected: int = 200
        avg_length_expected: float = 45.7
        empty_ratio_expected: float = 0.02

        # Act
        stats: TextStats = TextStats(
            min_length=min_length_expected,
            max_length=max_length_expected,
            avg_length=avg_length_expected,
            empty_ratio=empty_ratio_expected,
        )

        # Assert
        assert stats.min_length == min_length_expected
        assert stats.max_length == max_length_expected
        assert stats.avg_length == avg_length_expected
        assert stats.empty_ratio == empty_ratio_expected


class TestBooleanStatsContract:
    """Testes de contrato para :class:`BooleanStats`."""

    def test_boolean_stats_creation(self) -> None:
        """Verifica que BooleanStats é criada com todos os campos."""
        # Arrange
        true_count_expected: int = 75
        false_count_expected: int = 25
        true_ratio_expected: float = 0.75

        # Act
        stats: BooleanStats = BooleanStats(
            true_count=true_count_expected,
            false_count=false_count_expected,
            true_ratio=true_ratio_expected,
        )

        # Assert
        assert stats.true_count == true_count_expected
        assert stats.false_count == false_count_expected
        assert stats.true_ratio == true_ratio_expected

    def test_boolean_stats_zero_total(self) -> None:
        """Verifica que true_ratio é 0.0 quando não há valores."""
        # Arrange
        ...

        # Act
        stats: BooleanStats = BooleanStats(
            true_count=0,
            false_count=0,
            true_ratio=0.0,
        )

        # Assert
        assert stats.true_ratio == 0.0
        assert stats.true_count == 0
        assert stats.false_count == 0
