"""Resultado completo da análise exploratória de dados."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from spark_eda.domain.entities.correlation import Correlation
from spark_eda.domain.entities.data_profile import DataProfile
from spark_eda.domain.entities.insight import Insight
from spark_eda.domain.entities.quality_score import QualityScore
from spark_eda.domain.entities.recommendation import Recommendation


@dataclass(frozen=True)
class DatasetAnalysis:
    """Resultado completo da análise exploratória de dados.

    Reúne o perfil do dataset, pontuação de qualidade, correlações identificadas,
    insights gerados e recomendações de ação.

    Attributes:
        profile: Perfil completo do dataset com metadados e estatísticas.
        quality: Pontuação de qualidade dos dados com dimensões e fatores.
        correlations: Lista de correlações calculadas entre pares de colunas.
        insights: Lista de insights gerados durante a análise.
        recommendations: Lista de recomendações de ação propostas.
        timestamps: Data e hora da geração desta análise.
    """

    profile: DataProfile
    quality: QualityScore
    correlations: list[Correlation]
    insights: list[Insight]
    recommendations: list[Recommendation]
    timestamps: datetime
