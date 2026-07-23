"""Categorias de recomendações geradas pela análise."""

from __future__ import annotations

from enum import Enum


class RecommendationCategory(Enum):
    """Enumeração das categorias de recomendação que podem ser geradas."""

    TYPE_FIX = "type_fix"
    NULL_TREATMENT = "null_treatment"
    OUTLIER_TREATMENT = "outlier_treatment"
    PERFORMANCE = "performance"
    SCHEMA = "schema"
    BUSINESS_RULE = "business_rule"
