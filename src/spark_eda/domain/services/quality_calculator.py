"""Calculadora de qualidade dos dados.

Orquestra a execução de todos os fatores de qualidade registrados
no :data:`~spark_eda.domain.services.quality_factors.FACTOR_REGISTRY`
e produz um :class:`~spark_eda.domain.entities.quality_score.QualityScore` consolidado.
"""

from __future__ import annotations

from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.quality_score import QualityDimension, QualityFactor, QualityScore
from spark_eda.domain.services.quality_factors import FACTOR_REGISTRY

DIMENSION_WEIGHTS: dict[str, float] = {
    "completeness": 0.25,
    "uniqueness": 0.20,
    "consistency": 0.20,
    "timeliness": 0.15,
    "accuracy": 0.20,
}
"""Peso de cada dimensão no cálculo da pontuação geral de qualidade.

Os pesos foram definidos considerando o impacto relativo de cada
dimensão na qualidade percebida dos dados:

* **Completude** (25%): dados faltantes são o problema mais frequente.
* **Unicidade** (20%): duplicatas distorcem análises e métricas.
* **Consistência** (20%): dados inconsistentes quebram a integridade.
* **Atualidade** (15%): peso menor pois nem todo dataset é temporal.
* **Acurácia** (20%): outliers e violações de regras de negócio.
"""


class QualityCalculator:
    """Calculadora de qualidade dos dados, sem estado.

    Centraliza a orquestração dos fatores registrados no
    :data:`~spark_eda.domain.services.quality_factors.FACTOR_REGISTRY`,
    agrupando-os por dimensão e computando pontuações consolidadas.
    """

    @staticmethod
    def _compute_dimension_score(
        dimension_name: str,
        factors: list[QualityFactor],
    ) -> QualityDimension:
        """Computa a pontuação de uma dimensão a partir de seus fatores.

        A pontuação da dimensão é a soma ponderada das contribuições
        individuais dos fatores, convertida para a escala 0-100.

        Args:
            dimension_name: Nome da dimensão de qualidade.
            factors: Lista de fatores calculados para esta dimensão.

        Returns:
            :class:`QualityDimension` com pontuação, peso, contribuição
            e a lista completa de fatores.
        """
        if not factors:
            return QualityDimension(
                name=dimension_name,
                score=100.0,
                weight=DIMENSION_WEIGHTS.get(dimension_name, 0.0),
                contribution=DIMENSION_WEIGHTS.get(dimension_name, 0.0) * 100.0,
                factors=[],
            )

        contributions_sum: float = sum(f.contribution for f in factors)

        dimension_score: float = contributions_sum * 100.0

        weight: float = DIMENSION_WEIGHTS.get(dimension_name, 0.0)
        contribution: float = dimension_score * weight

        return QualityDimension(
            name=dimension_name,
            score=round(dimension_score, 2),
            weight=weight,
            contribution=round(contribution, 2),
            factors=factors,
        )

    @staticmethod
    def _compute_penalizer_impact(
        factor: QualityFactor,
        dimension_weight: float,
    ) -> float:
        """Calcula o impacto real de um fator na pontuação geral.

        O impacto é a perda potencial causada pelo fator,
        considerando seu peso interno dentro da dimensão e o
        peso da dimensão na pontuação geral.

        Args:
            factor: Fator de qualidade avaliado.
            dimension_weight: Peso da dimensão na pontuação geral.

        Returns:
            Valor numérico representando o impacto (perda de pontuação)
            na pontuação geral, em [0.0, 100.0].
        """
        return round(
            (1.0 - factor.score) * factor.internal_weight * dimension_weight * 100.0,
            2,
        )

    def calculate(self, profile: DataProfile) -> QualityScore:
        """Calcula a pontuação completa de qualidade para o dataset.

        1. Itera :data:`FACTOR_REGISTRY` executando cada função
           de cálculo de fator.
        2. Agrupa fatores por dimensão e computa pontuações.
        3. Calcula a pontuação geral como a soma ponderada das dimensões.
        4. Identifica os 5 fatores mais penalizadores.

        Args:
            profile: Perfil completo do dataset.

        Returns:
            :class:`QualityScore` com pontuação geral, dimensões e
            *top 5 penalizadores*.
        """
        factors_by_dimension: dict[str, list[QualityFactor]] = {}
        all_factors: list[tuple[str, QualityFactor]] = []

        for dimension_name, calculate_func in FACTOR_REGISTRY.items():
            factors: list[QualityFactor] = calculate_func(profile)
            factors_by_dimension[dimension_name] = factors
            for factor in factors:
                all_factors.append((dimension_name, factor))

        dimensions: dict[str, QualityDimension] = {}
        for dimension_name, factors in factors_by_dimension.items():
            dimensions[dimension_name] = self._compute_dimension_score(
                dimension_name=dimension_name,
                factors=factors,
            )

        overall: float = round(
            sum(dim.contribution for dim in dimensions.values()),
            2,
        )

        penalizers_with_impact: list[tuple[float, str, QualityFactor]] = []
        for dimension_name, factor in all_factors:
            dim_weight: float = DIMENSION_WEIGHTS.get(dimension_name, 0.0)
            impact: float = self._compute_penalizer_impact(factor, dim_weight)
            penalizers_with_impact.append((impact, dimension_name, factor))

        penalizers_with_impact.sort(key=lambda item: item[0], reverse=True)

        top_penalizers: list[QualityFactor] = [factor for _, _, factor in penalizers_with_impact[:5]]

        return QualityScore(
            overall=overall,
            dimensions=dimensions,
            top_penalizers=top_penalizers,
        )
